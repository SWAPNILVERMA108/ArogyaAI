from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ("id", "role", "content", "created_at")
        read_only_fields = fields


class ConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "title", "message_count", "created_at", "updated_at")
        read_only_fields = fields


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "title", "messages", "created_at", "updated_at")
        read_only_fields = fields


class ConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ("id", "title", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {"title": {"required": False}}


class ChatMessageRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=4000, trim_whitespace=True)
    conversation_id = serializers.IntegerField(required=False, min_value=1)


class ChatMessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    conversation_id = serializers.IntegerField()
    disclaimer = serializers.CharField()
    sources = serializers.ListField(child=serializers.DictField())
