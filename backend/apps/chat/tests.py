import json
import os
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ai.llm.gemini import GeminiClient, LLMProviderError
from .models import Conversation, Message
from .services import ChatHistoryService


User = get_user_model()


class ChatHistoryAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="chat-user@example.com", name="Chat User", password="StrongPass123!"
        )
        self.other_user = User.objects.create_user(
            email="other-chat-user@example.com", name="Other Chat User", password="StrongPass123!"
        )
        self.client.force_authenticate(self.user)

    def test_user_can_create_list_and_retrieve_conversations(self):
        created = self.client.post(
            reverse("chat:conversations"), {"title": "My symptoms"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        conversation_id = created.data["data"]["id"]
        self.assertEqual(created.data["data"]["title"], "My symptoms")
        self.assertEqual(created.data["data"]["messages"], [])

        listed = self.client.get(reverse("chat:conversations"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data["data"]), 1)
        self.assertEqual(listed.data["data"][0]["message_count"], 0)

        retrieved = self.client.get(reverse("chat:conversation-detail", args=[conversation_id]))
        self.assertEqual(retrieved.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieved.data["data"]["id"], conversation_id)

    def test_conversation_messages_are_returned_in_chronological_order(self):
        conversation = Conversation.objects.create(user=self.user, title="History")
        first = ChatHistoryService.add_message(conversation, Message.Role.USER, "I have a headache.")
        second = ChatHistoryService.add_message(
            conversation,
            Message.Role.ASSISTANT,
            "I can share general information, but cannot diagnose.",
        )

        response = self.client.get(reverse("chat:conversation-detail", args=[conversation.pk]))
        messages = response.data["data"]["messages"]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([message["id"] for message in messages], [first.id, second.id])
        self.assertEqual([message["role"] for message in messages], ["user", "assistant"])

    def test_user_can_clear_messages_without_deleting_conversation(self):
        conversation = Conversation.objects.create(user=self.user)
        ChatHistoryService.add_message(conversation, Message.Role.USER, "Question")

        response = self.client.delete(
            reverse("chat:conversation-messages", args=[conversation.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["deleted_messages"], 1)
        self.assertTrue(Conversation.objects.filter(pk=conversation.pk).exists())
        self.assertFalse(conversation.messages.exists())

    def test_user_can_rename_and_delete_conversation(self):
        conversation = Conversation.objects.create(user=self.user, title="Original")
        updated = self.client.patch(
            reverse("chat:conversation-detail", args=[conversation.pk]),
            {"title": "Updated"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["data"]["title"], "Updated")

        deleted = self.client.delete(reverse("chat:conversation-detail", args=[conversation.pk]))
        self.assertEqual(deleted.status_code, status.HTTP_200_OK)
        self.assertFalse(Conversation.objects.filter(pk=conversation.pk).exists())

    def test_users_cannot_access_each_others_conversations(self):
        conversation = Conversation.objects.create(user=self.other_user, title="Private")
        response = self.client.get(reverse("chat:conversation-detail", args=[conversation.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(reverse("chat:conversation-messages", args=[conversation.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        listed = self.client.get(reverse("chat:conversations"))
        self.assertEqual(listed.data["data"], [])

    def test_chat_history_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("chat:conversations"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatMessageAPITests(APITestCase):
    message_url = reverse("chat:message")

    def setUp(self):
        self.user = User.objects.create_user(
            email="ai-chat-user@example.com", name="AI Chat User", password="StrongPass123!"
        )
        self.other_user = User.objects.create_user(
            email="ai-chat-other@example.com", name="Other AI User", password="StrongPass123!"
        )
        self.client.force_authenticate(self.user)

    @patch("ai.llm.gemini.GeminiClient.generate", return_value="This is general information.")
    def test_message_creates_conversation_and_persists_both_turns(self, generate):
        response = self.client.post(
            self.message_url,
            {"message": "I have had a mild headache since this morning."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["message"], "This is general information.")
        self.assertIn("not a diagnosis", data["disclaimer"])
        conversation = Conversation.objects.get(pk=data["conversation_id"], user=self.user)
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(
            list(conversation.messages.values_list("role", flat=True)),
            [Message.Role.USER, Message.Role.ASSISTANT],
        )
        self.assertIn("not a doctor", generate.call_args.kwargs["system_instruction"])

    @patch("ai.llm.gemini.GeminiClient.generate", return_value="Please contact a clinician.")
    def test_existing_conversation_context_is_sent_in_order(self, generate):
        conversation = Conversation.objects.create(user=self.user, title="Earlier question")
        ChatHistoryService.add_message(conversation, Message.Role.USER, "I have a cough.")
        ChatHistoryService.add_message(conversation, Message.Role.ASSISTANT, "How long have you had it?")

        response = self.client.post(
            self.message_url,
            {"message": "For two days.", "conversation_id": conversation.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["conversation_id"], conversation.id)
        contents = generate.call_args.kwargs["contents"]
        self.assertEqual([item["role"] for item in contents], ["user", "model", "user"])
        self.assertIn("User question:\nFor two days.", contents[-1]["parts"][0]["text"])
        self.assertEqual(conversation.messages.count(), 4)

    def test_foreign_conversation_is_not_accessible_and_no_model_call_is_made(self):
        conversation = Conversation.objects.create(user=self.other_user, title="Private")
        with patch("ai.llm.gemini.GeminiClient.generate") as generate:
            response = self.client.post(
                self.message_url,
                {"message": "Question", "conversation_id": conversation.id},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        generate.assert_not_called()

    def test_invalid_or_blank_message_is_rejected(self):
        blank = self.client.post(self.message_url, {"message": "  "}, format="json")
        self.assertEqual(blank.status_code, status.HTTP_400_BAD_REQUEST)

        too_long = self.client.post(self.message_url, {"message": "x" * 4001}, format="json")
        self.assertEqual(too_long.status_code, status.HTTP_400_BAD_REQUEST)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "", "LLM_PROVIDER": "gemini"})
    def test_missing_provider_key_returns_service_unavailable_without_storing_content(self):
        response = self.client.post(self.message_url, {"message": "Question"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(Conversation.objects.filter(user=self.user).count(), 0)

    @patch("ai.llm.gemini.GeminiClient.generate", side_effect=LLMProviderError("failure"))
    def test_provider_failure_is_reported_without_fabricating_or_storing_an_answer(self, generate):
        response = self.client.post(self.message_url, {"message": "Question"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(Conversation.objects.filter(user=self.user).count(), 0)
        generate.assert_called_once()

    @patch.dict(os.environ, {"LLM_PROVIDER": "unknown-provider"})
    def test_unsupported_provider_returns_service_unavailable(self):
        response = self.client.post(self.message_url, {"message": "Question"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("ai.llm.gemini.urlopen")
    def test_gemini_client_uses_authenticated_generate_content_rest_request(self, urlopen):
        fake_response = MagicMock()
        fake_response.__enter__.return_value.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": "A response."}]}}]}
        ).encode("utf-8")
        urlopen.return_value = fake_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "test-model"}):
            answer = GeminiClient().generate(
                contents=[{"role": "user", "parts": [{"text": "hello"}]}],
                system_instruction="Safe assistant instructions",
            )

        self.assertEqual(answer, "A response.")
        request = urlopen.call_args.args[0]
        self.assertIn("/models/test-model:generateContent", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-key")
        payload = json.loads(request.data)
        self.assertEqual(payload["contents"][0]["parts"][0]["text"], "hello")
        self.assertEqual(payload["system_instruction"]["parts"][0]["text"], "Safe assistant instructions")

    @patch("ai.llm.gemini.GeminiClient.generate", return_value="See a clinician if concerned.")
    @patch(
        "ai.services.chat_service.RAGPipeline.retrieve",
        return_value=[
            {
                "text": "Reviewed reference excerpt.",
                "source": "guide.pdf",
                "page": 3,
                "chunk_index": 0,
                "start_index": 0,
                "score": 0.91,
            }
        ],
    )
    def test_message_includes_retrieved_excerpt_and_returns_citation(self, retrieve, generate):
        response = self.client.post(
            self.message_url, {"message": "Question"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prompt = generate.call_args.kwargs["contents"][-1]["parts"][0]["text"]
        self.assertIn("Reviewed reference excerpt.", prompt)
        self.assertIn("guide.pdf, page 3", prompt)
        self.assertEqual(response.data["data"]["sources"], [{"source": "guide.pdf", "page": 3}])


class MedicalRAGTests(APITestCase):
    def test_chunking_and_faiss_round_trip_in_temporary_index(self):
        import tempfile
        from pathlib import Path

        import numpy as np
        from langchain_core.documents import Document

        from ai.rag.chunker import chunk_documents
        from ai.rag.pipeline import RAGPipeline
        from ai.rag.vector_store import FaissVectorStore

        class FakeEmbeddings:
            def embed_documents(self, texts):
                return np.tile(np.array([[1.0, 0.0]], dtype=np.float32), (len(texts), 1))

            def embed_query(self, text):
                return np.array([[1.0, 0.0]], dtype=np.float32)

        source_text = "Reviewed reference passage. " * 100
        chunks = chunk_documents(
            [Document(page_content=source_text, metadata={"source": "guide.md"})],
            chunk_size=120,
            chunk_overlap=20,
        )
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["source"], "guide.md")
        self.assertEqual(chunks[0].metadata["chunk_index"], 0)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "medical"
            source_dir.mkdir()
            (source_dir / "guide.md").write_text(source_text, encoding="utf-8")
            pipeline = RAGPipeline(
                documents_dir=source_dir,
                index_dir=root / "index",
                embeddings=FakeEmbeddings(),
            )

            summary = pipeline.ingest()
            found = pipeline.retrieve("query")

        self.assertEqual(summary["source_documents"], 1)
        self.assertGreater(summary["chunks"], 1)
        self.assertTrue(found)
        self.assertEqual(found[0]["source"], "guide.md")
        self.assertIn("Reviewed reference passage.", RAGPipeline.format_context(found))
        self.assertEqual(RAGPipeline.source_references(found), [{"source": "guide.md"}])

    def test_retriever_returns_empty_when_no_index_exists(self):
        import tempfile
        from pathlib import Path

        from ai.rag.retriever import MedicalRetriever
        from ai.rag.vector_store import FaissVectorStore

        with tempfile.TemporaryDirectory() as temp_dir:
            retriever = MedicalRetriever(vector_store=FaissVectorStore(Path(temp_dir)))
            self.assertEqual(retriever.search("question"), [])
