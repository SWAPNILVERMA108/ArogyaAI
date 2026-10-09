from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from common.utils.responses import success_response
from ai.services.chat_service import ChatService

from .models import Conversation
from .serializers import (
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    ChatMessageRequestSerializer,
    ChatMessageResponseSerializer,
)
from .services import ChatHistoryService


class ConversationCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Chat"],
        request=None,
        responses={200: ConversationListSerializer(many=True)},
    )
    def get(self, request):
        conversations = ChatHistoryService.list_conversations(request.user)
        return success_response(
            ConversationListSerializer(conversations, many=True).data,
            "Conversations retrieved successfully.",
        )

    @extend_schema(
        tags=["Chat"],
        request=ConversationCreateSerializer,
        responses={201: ConversationDetailSerializer},
    )
    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = ChatHistoryService.create_conversation(
            request.user,
            serializer.validated_data.get("title", "New conversation"),
        )
        return success_response(
            ConversationDetailSerializer(conversation).data,
            "Conversation created successfully.",
            status.HTTP_201_CREATED,
        )


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_conversation(self, request, pk):
        return get_object_or_404(
            Conversation.objects.prefetch_related("messages"),
            pk=pk,
            user=request.user,
        )

    @extend_schema(tags=["Chat"], request=None, responses={200: ConversationDetailSerializer})
    def get(self, request, pk):
        conversation = self.get_conversation(request, pk)
        return success_response(
            ConversationDetailSerializer(conversation).data,
            "Conversation retrieved successfully.",
        )

    @extend_schema(
        tags=["Chat"],
        request=ConversationCreateSerializer,
        responses={200: ConversationDetailSerializer},
    )
    def patch(self, request, pk):
        conversation = self.get_conversation(request, pk)
        serializer = ConversationCreateSerializer(
            conversation,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        return success_response(
            ConversationDetailSerializer(conversation).data,
            "Conversation updated successfully.",
        )

    @extend_schema(tags=["Chat"], request=None, responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        conversation = self.get_conversation(request, pk)
        ChatHistoryService.delete_conversation(conversation)
        return success_response(None, "Conversation deleted successfully.")


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get_conversation(self, request, pk):
        return get_object_or_404(Conversation, pk=pk, user=request.user)

    @extend_schema(tags=["Chat"], request=None, responses={200: OpenApiTypes.OBJECT})
    def delete(self, request, pk):
        conversation = self.get_conversation(request, pk)
        deleted_count = ChatHistoryService.clear_messages(conversation)
        return success_response(
            {"deleted_messages": deleted_count},
            "Conversation messages cleared successfully.",
        )


class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    @extend_schema(
        tags=["Chat"],
        request=ChatMessageRequestSerializer,
        responses={200: ChatMessageResponseSerializer},
    )
    def post(self, request):
        serializer = ChatMessageRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = ChatService.respond(
            user=request.user,
            message=serializer.validated_data["message"],
            conversation_id=serializer.validated_data.get("conversation_id"),
        )
        return success_response(result, "Response generated successfully.")
