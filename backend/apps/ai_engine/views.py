"""
CALDIM Consultation Engine API Views.
Exposes secure conversation endpoints requiring visitor context token authentication,
supports multi-turn architectural consultations, dynamic questions, and message idempotency.
"""
import hashlib
import logging
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed
from rest_framework.throttling import ScopedRateThrottle

from apps.visitors.models import (
    Visitor,
    ProfileCompletionStatus,
    ConsentCategory,
    ConsentStatus,
)
from apps.ai_engine.models import Conversation, ConsultationMessage, ConversationStatus
from apps.ai_engine.serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    ConversationCreateSerializer,
    MessageCreateSerializer,
    ConsultationMessageSerializer,
)
from apps.ai_engine.services.orchestration import ConsultationOrchestrationService
from apps.ai_engine.exceptions import AIProviderError

logger = logging.getLogger(__name__)


def resolve_authenticated_visitor(request) -> Visitor:
    """
    Extracts and validates visitor token from X-Visitor-Token or Authorization: Bearer header.
    Resolves visitor record via indexed SHA-256 token hash and enforces revocation and TTL rules.
    """
    token = request.headers.get("X-Visitor-Token", "").strip()
    if not token:
        auth_header = request.headers.get("Authorization", "").strip()
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise NotAuthenticated("A valid X-Visitor-Token or Bearer token is required to access consultations.")

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    visitor = Visitor.objects.filter(access_token_hash=token_hash, token_revoked_at__isnull=True).first()

    if not visitor or not visitor.verify_access_token(token):
        raise AuthenticationFailed("Invalid, revoked, or expired visitor token.")

    return visitor


class ConversationListCreateView(APIView):
    """
    GET  /api/v1/consultations/ - List all consultations owned by the authenticated visitor.
    POST /api/v1/consultations/ - Start a new consultation challenge with initial message.
    """
    authentication_classes = []
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "consultation_turn"

    def get(self, request, *args, **kwargs):
        try:
            visitor = resolve_authenticated_visitor(request)
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except AuthenticationFailed as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        conversations = Conversation.objects.filter(visitor=visitor).order_by("-created_at")
        serializer = ConversationListSerializer(conversations, many=True)
        return Response(
            {
                "count": conversations.count(),
                "conversations": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        try:
            visitor = resolve_authenticated_visitor(request)
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except AuthenticationFailed as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        serializer = ConversationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Enforce mandatory onboarding before starting consultation
        if visitor.profile_completion_status != ProfileCompletionStatus.COMPLETE:
            return Response(
                {
                    "detail": "Conversational onboarding must be completed before initiating an industrial consultation.",
                    "code": "ONBOARDING_INCOMPLETE",
                    "profile_completion_status": visitor.profile_completion_status,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Enforce essential processing consent
        has_essential_consent = visitor.consents.filter(
            category=ConsentCategory.ESSENTIAL,
            status=ConsentStatus.GRANTED,
            revoked_at__isnull=True,
        ).exists()
        if not has_essential_consent:
            return Response(
                {
                    "detail": "Essential service processing consent is required to start a consultation.",
                    "code": "CONSENT_REQUIRED",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        title = serializer.validated_data.get("title", "").strip()
        initial_message = serializer.validated_data["initial_message"]
        client_message_id = serializer.validated_data.get("client_message_id", "").strip()

        # Create new conversation for visitor
        conversation = Conversation.objects.create(
            visitor=visitor,
            title=title or "Industrial AI Consultation",
            status=ConversationStatus.ACTIVE,
        )

        try:
            assistant_msg = ConsultationOrchestrationService.execute_turn(
                conversation=conversation,
                user_content=initial_message,
                client_message_id=client_message_id,
            )
        except AIProviderError as e:
            logger.error("AI provider error during initial turn: %s", e)
            return Response(
                {
                    "error": "The AI consultation service encountered an issue generating a response.",
                    "details": str(e),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.exception("Unexpected error during initial turn: %s", e)
            return Response(
                {"error": "An internal error occurred during consultation generation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Refresh conversation to fetch updated title, state, and messages
        conversation.refresh_from_db()
        response_serializer = ConversationSerializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    """
    GET /api/v1/consultations/<uuid:conversation_id>/ - Retrieve conversation profile & messages.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, conversation_id, *args, **kwargs):
        try:
            visitor = resolve_authenticated_visitor(request)
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except AuthenticationFailed as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        conversation = get_object_or_404(
            Conversation.objects.prefetch_related("messages"),
            id=conversation_id,
            visitor=visitor,
        )
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConversationMessageCreateView(APIView):
    """
    POST /api/v1/consultations/<uuid:conversation_id>/messages/ - Submit follow-up turn.
    """
    authentication_classes = []
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "consultation_turn"

    def post(self, request, conversation_id, *args, **kwargs):
        try:
            visitor = resolve_authenticated_visitor(request)
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except AuthenticationFailed as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            visitor=visitor,
        )

        serializer = MessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        content = serializer.validated_data["content"]
        client_message_id = serializer.validated_data.get("client_message_id", "").strip()

        try:
            assistant_msg = ConsultationOrchestrationService.execute_turn(
                conversation=conversation,
                user_content=content,
                client_message_id=client_message_id,
            )
        except AIProviderError as e:
            logger.error("AI provider error during message turn: %s", e)
            return Response(
                {
                    "error": "The AI consultation service encountered an issue generating a response.",
                    "details": str(e),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            logger.exception("Unexpected error during message turn: %s", e)
            return Response(
                {"error": "An internal error occurred during consultation generation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        conversation.refresh_from_db()
        return Response(
            {
                "conversation_id": str(conversation.id),
                "consultation_state": conversation.consultation_state,
                "assistant_message": ConsultationMessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_200_OK,
        )
