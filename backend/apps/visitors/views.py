import secrets
import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, NotAuthenticated

from .models import (
    Visitor,
    VisitorConsent,
    VisitorSession,
    ConsentCategory,
    ConsentStatus,
    SessionStatus,
)
from .serializers import (
    VisitorCreateSerializer,
    VisitorUpdateSerializer,
    VisitorResponseSerializer,
    VisitorConsentSerializer,
    VisitorConsentCreateSerializer,
    VisitorSessionSerializer,
    VisitorSessionCreateSerializer,
)

from rest_framework.throttling import ScopedRateThrottle

logger = logging.getLogger(__name__)

def get_visitor_token_from_request(request) -> str:
    """Extract visitor token from X-Visitor-Token or Authorization: Bearer header."""
    token = request.headers.get("X-Visitor-Token", "").strip()
    if not token:
        auth_header = request.headers.get("Authorization", "").strip()
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    return token

def verify_visitor_access(visitor: Visitor, request) -> None:
    """Verify client token matches stored visitor access hash."""
    token = get_visitor_token_from_request(request)
    if not token or not visitor.verify_access_token(token):
        raise NotAuthenticated("Valid visitor context token is required to access this profile.")

class VisitorCreateView(APIView):
    """
    POST /api/v1/visitors/
    Validate and create a visitor profile with optional initial consent records.
    Public listing is strictly forbidden (GET returns 405 Method Not Allowed).
    Protected against bot floods via configurable anonymous rate limiting.
    """
    authentication_classes = []
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "visitor_create"

    def get(self, request, *args, **kwargs):
        return Response(
            {"detail": "Public visitor listing is not permitted."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def post(self, request, *args, **kwargs):
        serializer = VisitorCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        initial_consents = validated_data.pop("initial_consents", [])

        # Generate secure ownership token returned only once upon creation
        raw_token = secrets.token_urlsafe(32)

        try:
            with transaction.atomic():
                visitor = Visitor(**validated_data)
                visitor.set_access_token(raw_token)
                visitor.update_completion_status()
                visitor.save()

                for consent_data in initial_consents:
                    VisitorConsent.objects.create(
                        visitor=visitor,
                        category=consent_data["category"],
                        status=consent_data.get("status", ConsentStatus.GRANTED),
                        policy_version=consent_data.get("policy_version", "1.0"),
                    )

            response_data = {
                "visitor": VisitorResponseSerializer(visitor).data,
                "access_token": raw_token,
                "message": "Visitor profile created successfully.",
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception:
            logger.exception("Failed to create visitor profile.")
            return Response(
                {"detail": "An internal error occurred while creating the visitor profile."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class VisitorDetailView(APIView):
    """
    GET /api/v1/visitors/{visitor_id}/
    Retrieve visitor profile context. Requires valid X-Visitor-Token header.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, visitor_id, *args, **kwargs):
        try:
            visitor = get_object_or_404(Visitor, id=visitor_id, archived_at__isnull=True)
            verify_visitor_access(visitor, request)

            active_consents = visitor.consents.filter(revoked_at__isnull=True)
            data = {
                "visitor": VisitorResponseSerializer(visitor).data,
                "consents": VisitorConsentSerializer(active_consents, many=True).data,
            }
            return Response(data, status=status.HTTP_200_OK)
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    def patch(self, request, visitor_id, *args, **kwargs):
        """
        PATCH /api/v1/visitors/{visitor_id}/
        Incrementally update visitor profile context during conversational onboarding.
        Requires proof of ownership via X-Visitor-Token.
        """
        try:
            visitor = get_object_or_404(Visitor, id=visitor_id, archived_at__isnull=True)
            verify_visitor_access(visitor, request)

            serializer = VisitorUpdateSerializer(visitor, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            visitor.update_completion_status()
            visitor.save()

            active_consents = visitor.consents.filter(revoked_at__isnull=True)
            data = {
                "visitor": VisitorResponseSerializer(visitor).data,
                "consents": VisitorConsentSerializer(active_consents, many=True).data,
                "message": "Visitor profile updated successfully.",
            }
            return Response(data, status=status.HTTP_200_OK)
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            logger.exception("Failed to update visitor profile.")
            return Response(
                {"detail": "An internal error occurred while updating the visitor profile."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class VisitorSessionCreateView(APIView):
    """
    POST /api/v1/visitors/{visitor_id}/sessions/
    Create a new consultation session for a verified visitor context.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, visitor_id, *args, **kwargs):
        try:
            visitor = get_object_or_404(Visitor, id=visitor_id, archived_at__isnull=True)
            verify_visitor_access(visitor, request)

            serializer = VisitorSessionCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            metadata = serializer.validated_data.get("metadata", {})
            session = VisitorSession.objects.create(
                visitor=visitor,
                status=SessionStatus.ACTIVE,
                metadata=metadata,
            )
            return Response(
                VisitorSessionSerializer(session).data,
                status=status.HTTP_201_CREATED,
            )
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            logger.exception("Failed to create visitor session.")
            return Response(
                {"detail": "An error occurred while creating the consultation session."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class VisitorConsentRecordView(APIView):
    """
    POST /api/v1/visitors/{visitor_id}/consent/
    Explicitly record or update visitor consent.
    Atomically revokes previous active consent for the given category before recording new status.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, visitor_id, *args, **kwargs):
        try:
            visitor = get_object_or_404(Visitor, id=visitor_id, archived_at__isnull=True)
            verify_visitor_access(visitor, request)

            serializer = VisitorConsentCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            category = serializer.validated_data["category"]
            consent_status = serializer.validated_data["status"]
            policy_version = serializer.validated_data.get("policy_version", "1.0")

            with transaction.atomic():
                # Revoke existing active consent records for this category
                now = timezone.now()
                VisitorConsent.objects.filter(
                    visitor=visitor,
                    category=category,
                    revoked_at__isnull=True,
                ).update(revoked_at=now)

                # Create the new consent record
                new_consent = VisitorConsent.objects.create(
                    visitor=visitor,
                    category=category,
                    status=consent_status,
                    policy_version=policy_version,
                )

            return Response(
                VisitorConsentSerializer(new_consent).data,
                status=status.HTTP_201_CREATED,
            )
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            logger.exception("Failed to update visitor consent.")
            return Response(
                {"detail": "An error occurred while recording consent."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class VisitorTokenRevokeView(APIView):
    """
    POST /api/v1/visitors/{visitor_id}/revoke-token/
    Revoke visitor session token (e.g. on visitor kiosk sign-out / reset).
    Requires proof of ownership via X-Visitor-Token.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, visitor_id, *args, **kwargs):
        try:
            visitor = get_object_or_404(Visitor, id=visitor_id, archived_at__isnull=True)
            verify_visitor_access(visitor, request)

            visitor.revoke_access_token()
            return Response(
                {
                    "detail": "Visitor access token revoked successfully.",
                    "revoked": True,
                    "token_revoked_at": visitor.token_revoked_at.isoformat() if visitor.token_revoked_at else None,
                },
                status=status.HTTP_200_OK,
            )
        except NotAuthenticated as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            logger.exception("Failed to revoke visitor token.")
            return Response(
                {"detail": "An error occurred while revoking the visitor token."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
