"""
CALDIM Consultation Engine Domain Models.
Persists multi-turn consultation conversations, structured architectural findings,
dynamic follow-up questions, and message provenance.
"""
import uuid
from django.db import models
from apps.visitors.models import Visitor


class ConversationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class Conversation(models.Model):
    """
    Persistent consultation conversation owned by a verified visitor.
    Supports multiple business challenges per visitor and maintains
    accumulated operational findings across consultation turns.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        related_name="conversations",
        db_index=True,
    )
    title = models.CharField(
        max_length=250,
        blank=True,
        default="Industrial AI Consultation",
        help_text="Descriptive summary of the operational challenge",
    )
    challenge_summary = models.TextField(
        blank=True,
        default="",
        help_text="Consolidated problem statement and operational context",
    )
    status = models.CharField(
        max_length=30,
        choices=ConversationStatus.choices,
        default=ConversationStatus.ACTIVE,
        db_index=True,
    )
    consultation_state = models.JSONField(
        blank=True,
        default=dict,
        help_text="Accumulated structured findings, pain points, and solution recommendations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "caldim_conversations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["visitor", "created_at"], name="idx_conv_visitor_created"),
            models.Index(fields=["status"], name="idx_conv_status"),
        ]

    def __str__(self):
        return f"Conversation: {self.title} ({self.status}) for Visitor {self.visitor_id}"


class ConsultationMessage(models.Model):
    """
    Individual message turn within a consultation conversation.
    Stores user input, model response, structured analysis findings,
    untrusted knowledge chunk citations, and token telemetry.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    role = models.CharField(
        max_length=20,
        choices=MessageRole.choices,
        db_index=True,
    )
    content = models.TextField(
        help_text="Natural language content of the message",
    )
    client_message_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="Client idempotency key to prevent duplicate turns on network retry",
    )
    structured_payload = models.JSONField(
        blank=True,
        default=dict,
        help_text="Structured analysis: findings, dynamic questions, recommendations, roadmap",
    )
    knowledge_sources = models.JSONField(
        blank=True,
        default=list,
        help_text="Attributed knowledge chunks retrieved during turn generation",
    )
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    model_id = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "caldim_consultation_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="idx_cmsg_conv_created"),
            models.Index(fields=["client_message_id"], name="idx_cmsg_client_id"),
        ]

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}... ({self.conversation_id})"
