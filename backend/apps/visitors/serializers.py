from rest_framework import serializers
from .models import (
    Visitor,
    VisitorConsent,
    VisitorSession,
    ProfileCompletionStatus,
    ConsentCategory,
    ConsentStatus,
    SessionStatus,
)

FORBIDDEN_METADATA_KEYS = {"password", "token", "secret", "auth", "credit_card", "ssn", "api_key"}

class VisitorConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorConsent
        fields = [
            "id",
            "category",
            "status",
            "policy_version",
            "recorded_at",
            "revoked_at",
        ]
        read_only_fields = ["id", "recorded_at", "revoked_at"]

class VisitorConsentCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=ConsentCategory.choices)
    status = serializers.ChoiceField(choices=ConsentStatus.choices, default=ConsentStatus.GRANTED)
    policy_version = serializers.CharField(max_length=50, default="1.0", required=False)

class VisitorResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = [
            "id",
            "display_name",
            "profession",
            "company_name",
            "industry",
            "department",
            "responsibilities",
            "email",
            "phone",
            "profile_completion_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "profile_completion_status", "created_at", "updated_at"]

class VisitorCreateSerializer(serializers.ModelSerializer):
    initial_consents = VisitorConsentCreateSerializer(many=True, required=False)

    class Meta:
        model = Visitor
        fields = [
            "display_name",
            "profession",
            "company_name",
            "industry",
            "department",
            "responsibilities",
            "email",
            "phone",
            "initial_consents",
        ]

    def validate_email(self, value):
        if value:
            value = value.strip().lower()
        return value

    def validate_phone(self, value):
        if value:
            value = value.strip()
            if len(value) < 6:
                raise serializers.ValidationError("Phone number must contain at least 6 digits.")
        return value

class VisitorUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for incremental profile updates during conversational onboarding.
    Validates field constraints, strips whitespace, and enforces phone country-code formatting.
    """
    class Meta:
        model = Visitor
        fields = [
            "display_name",
            "profession",
            "company_name",
            "industry",
            "department",
            "responsibilities",
            "email",
            "phone",
        ]

    def validate_email(self, value):
        if value:
            value = value.strip().lower()
        return value

    def validate_phone(self, value):
        if value:
            value = value.strip()
            import re
            if len(value) < 6 or not re.match(r"^\+?[0-9\s\-().]{6,25}$", value):
                raise serializers.ValidationError(
                    "Phone number must contain at least 6 digits and a valid country code (e.g., +1, +91)."
                )
        return value

    def validate_display_name(self, value):
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Full name must be at least 2 characters.")
        return value

    def validate_profession(self, value):
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Profession or job title must be at least 2 characters.")
        return value

    def validate_company_name(self, value):
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Company name must be at least 2 characters.")
        return value

    def validate_industry(self, value):
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Industry must be at least 2 characters.")
        return value

class VisitorSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorSession
        fields = [
            "id",
            "visitor_id",
            "status",
            "created_at",
            "last_activity_at",
            "ended_at",
            "metadata",
        ]
        read_only_fields = ["id", "visitor_id", "status", "created_at", "last_activity_at", "ended_at"]

class VisitorSessionCreateSerializer(serializers.Serializer):
    metadata = serializers.DictField(required=False, default=dict)

    def validate_metadata(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata must be a JSON dictionary.")
        # Filter out sensitive or forbidden operational keys
        cleaned = {}
        for k, v in value.items():
            k_lower = str(k).lower()
            if any(forbidden in k_lower for forbidden in FORBIDDEN_METADATA_KEYS):
                continue
            if isinstance(v, (str, int, float, bool)):
                cleaned[str(k)[:50]] = v
        return cleaned
