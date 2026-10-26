"""
CALDIM Consultation Engine Serializers.
Provides structured request validation and response formatting for conversations,
consultation turns, dynamic questions, and architectural recommendations.
"""
from rest_framework import serializers
from apps.ai_engine.models import Conversation, ConsultationMessage


class ConsultationMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for individual consultation message turns.
    """
    class Meta:
        model = ConsultationMessage
        fields = [
            "id",
            "role",
            "content",
            "client_message_id",
            "structured_payload",
            "knowledge_sources",
            "prompt_tokens",
            "completion_tokens",
            "latency_ms",
            "model_id",
            "created_at",
        ]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    """
    Detailed conversation serializer with full message history.
    """
    messages = ConsultationMessageSerializer(many=True, read_only=True)
    visitor_id = serializers.UUIDField(source="visitor.id", read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "visitor_id",
            "title",
            "challenge_summary",
            "status",
            "consultation_state",
            "created_at",
            "updated_at",
            "messages",
        ]
        read_only_fields = fields


class ConversationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing conversations of a visitor.
    """
    visitor_id = serializers.UUIDField(source="visitor.id", read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "visitor_id",
            "title",
            "challenge_summary",
            "status",
            "message_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_message_count(self, obj) -> int:
        return obj.messages.count()


class ConversationCreateSerializer(serializers.Serializer):
    """
    Validates initial request to start a new consultation conversation.
    """
    title = serializers.CharField(max_length=250, required=False, allow_blank=True, default="")
    initial_message = serializers.CharField(min_length=3, max_length=10000, required=True)
    client_message_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")


class MessageCreateSerializer(serializers.Serializer):
    """
    Validates follow-up message turns submitted by visitors.
    """
    content = serializers.CharField(min_length=2, max_length=10000, required=True)
    client_message_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
