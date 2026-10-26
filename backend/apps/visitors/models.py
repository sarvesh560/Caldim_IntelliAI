import uuid
import hashlib
import secrets
import datetime
from django.db import models
from django.utils import timezone
from django.conf import settings

class ProfileCompletionStatus(models.TextChoices):
    INCOMPLETE = "incomplete", "Incomplete"
    PARTIAL = "partial", "Partial"
    COMPLETE = "complete", "Complete"

class ConsentCategory(models.TextChoices):
    ESSENTIAL = "essential", "Essential Service Processing"
    EMAIL_CONTACT = "email_contact", "Direct Email Contact"
    ANALYTICS = "analytics", "Usage Analytics & Personalization"
    PROPOSAL_DELIVERY = "proposal_delivery", "Proposal Communications"
    MARKETING = "marketing", "Marketing Updates & Product Announcements"

class ConsentStatus(models.TextChoices):
    GRANTED = "granted", "Granted"
    DENIED = "denied", "Denied"

class SessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    IDLE = "idle", "Idle"
    ENDED = "ended", "Ended"
    EXPIRED = "expired", "Expired"

class Visitor(models.Model):
    """
    Persistent professional profile for a CALDIM visitor.
    Supports conversational onboarding with optional profile fields at initial creation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=150, blank=True, default="")
    profession = models.CharField(max_length=150, blank=True, default="", help_text="Job title or designation")
    company_name = models.CharField(max_length=200, blank=True, default="")
    industry = models.CharField(max_length=150, blank=True, default="")
    department = models.CharField(max_length=150, blank=True, default="")
    responsibilities = models.TextField(blank=True, default="", help_text="Business responsibilities or professional context")
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    profile_completion_status = models.CharField(
        max_length=20,
        choices=ProfileCompletionStatus.choices,
        default=ProfileCompletionStatus.INCOMPLETE,
        db_index=True
    )

    # Secure verification hash to prevent arbitrary UUID access; raw token is never persisted
    access_token_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="SHA-256 hash of client context access token"
    )

    token_created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Timestamp when current access token was generated"
    )
    token_revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp when the access token was explicitly revoked"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "caldim_visitors"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"], name="idx_visitor_created_at"),
            models.Index(fields=["profile_completion_status"], name="idx_visitor_status"),
            models.Index(fields=["token_revoked_at"], name="idx_visitor_token_revoked"),
        ]

    def __str__(self):
        name = self.display_name or self.profession or str(self.id)[:8]
        company = f" @ {self.company_name}" if self.company_name else ""
        return f"Visitor: {name}{company}"

    def set_access_token(self, raw_token: str) -> None:
        """Hash and store access token securely using SHA-256, recording generation timestamp."""
        self.access_token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
        self.token_created_at = timezone.now()
        self.token_revoked_at = None

    def revoke_access_token(self) -> None:
        """Revoke current access token without modifying or deleting visitor data."""
        self.token_revoked_at = timezone.now()
        self.save(update_fields=["token_revoked_at", "updated_at"])

    def verify_access_token(self, raw_token: str) -> bool:
        """
        Verify client token against stored SHA-256 digest using constant-time comparison,
        enforcing revocation and configurable expiration checks.
        """
        if not self.access_token_hash or not raw_token:
            return False

        # 1. Reject if token was explicitly revoked
        if self.token_revoked_at is not None:
            return False

        # 2. Reject if token has expired based on configurable TTL
        ttl_days = getattr(settings, "VISITOR_TOKEN_TTL_DAYS", 30)
        if ttl_days > 0:
            reference_time = self.token_created_at or self.created_at
            if reference_time:
                expiry_time = reference_time + datetime.timedelta(days=ttl_days)
                if timezone.now() > expiry_time:
                    return False

        # 3. Constant-time digest comparison to prevent timing side-channels
        candidate_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
        return secrets.compare_digest(candidate_hash, self.access_token_hash)

    def update_completion_status(self) -> None:
        """Calculate and update completion state based on filled fields."""
        has_basic = bool(self.display_name and self.profession)
        has_business = bool(self.company_name and self.industry and (self.department or self.responsibilities))
        has_contact = bool(self.email)

        if has_basic and has_business and has_contact:
            self.profile_completion_status = ProfileCompletionStatus.COMPLETE
        elif bool(self.display_name or self.profession or self.company_name or self.industry or self.email or self.phone):
            self.profile_completion_status = ProfileCompletionStatus.PARTIAL
        else:
            self.profile_completion_status = ProfileCompletionStatus.INCOMPLETE

class VisitorConsent(models.Model):
    """
    Explicit GDPR/Privacy consent records for a visitor.
    Separate from visitor profile to prevent inferring marketing consent from contact info.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="consents")
    category = models.CharField(max_length=50, choices=ConsentCategory.choices, db_index=True)
    status = models.CharField(max_length=20, choices=ConsentStatus.choices, default=ConsentStatus.GRANTED)
    policy_version = models.CharField(max_length=50, default="1.0")
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "caldim_visitor_consents"
        ordering = ["-recorded_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["visitor", "category"],
                condition=models.Q(revoked_at__isnull=True),
                name="unique_active_consent_per_category"
            )
        ]
        indexes = [
            models.Index(fields=["visitor", "category", "revoked_at"], name="idx_consent_active_lookup"),
        ]

    def __str__(self):
        state = "Active" if not self.revoked_at else "Revoked"
        return f"{self.visitor_id} | {self.get_category_display()}: {self.status} ({state})"

    def revoke(self) -> None:
        """Mark consent as revoked."""
        if not self.revoked_at:
            self.revoked_at = timezone.now()
            self.save(update_fields=["revoked_at"])

class VisitorSession(models.Model):
    """
    Represents an individual kiosk or browser consultation session.
    Distinguishes ephemeral visits from the visitor's persistent profile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="sessions")
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.ACTIVE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Non-sensitive operational session metadata (e.g. user-agent, screen size, referral source)"
    )

    class Meta:
        db_table = "caldim_visitor_sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["visitor", "status"], name="idx_session_visitor_status"),
        ]

    def __str__(self):
        return f"Session {str(self.id)[:8]} ({self.visitor_id}) - {self.status}"

    def end_session(self) -> None:
        """Gracefully terminate consultation session."""
        self.status = SessionStatus.ENDED
        self.ended_at = timezone.now()
        self.save(update_fields=["status", "ended_at"])
