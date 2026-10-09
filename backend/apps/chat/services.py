from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from .models import Conversation, Message


class ChatHistoryService:
    @staticmethod
    def list_conversations(user):
        return Conversation.objects.filter(user=user).annotate(
            message_count=Count("messages")
        )

    @staticmethod
    def create_conversation(user, title="New conversation"):
        return Conversation.objects.create(user=user, title=title)

    @staticmethod
    def get_conversation(user, conversation_id):
        return Conversation.objects.prefetch_related("messages").get(
            user=user,
            pk=conversation_id,
        )

    @staticmethod
    def clear_messages(conversation):
        with transaction.atomic():
            deleted_count, _ = conversation.messages.all().delete()
            Conversation.objects.filter(pk=conversation.pk).update(updated_at=timezone.now())
        return deleted_count

    @staticmethod
    def delete_conversation(conversation):
        conversation.delete()

    @staticmethod
    def add_message(conversation, role, content):
        """Persist one validated message and update conversation recency.

        The AI message endpoint in a later chunk will use this method after the
        request and generated response have passed their respective validation.
        """
        with transaction.atomic():
            message = Message.objects.create(
                conversation=conversation,
                role=role,
                content=content,
            )
            Conversation.objects.filter(pk=conversation.pk).update(updated_at=timezone.now())
        return message
