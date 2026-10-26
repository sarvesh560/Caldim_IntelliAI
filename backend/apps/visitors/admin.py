from django.contrib import admin
from .models import Visitor, VisitorConsent, VisitorSession

class VisitorConsentInline(admin.TabularInline):
    model = VisitorConsent
    extra = 0
    readonly_fields = ["recorded_at", "revoked_at"]
    can_delete = False

class VisitorSessionInline(admin.TabularInline):
    model = VisitorSession
    extra = 0
    readonly_fields = ["id", "created_at", "last_activity_at", "ended_at"]
    can_delete = False

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "display_name",
        "profession",
        "company_name",
        "profile_completion_status",
        "created_at",
    ]
    list_filter = [
        "profile_completion_status",
        "industry",
        "created_at",
    ]
    search_fields = [
        "id",
        "display_name",
        "profession",
        "company_name",
        "department",
    ]
    readonly_fields = [
        "id",
        "access_token_hash",
        "token_created_at",
        "token_revoked_at",
        "created_at",
        "updated_at",
    ]
    inlines = [VisitorConsentInline, VisitorSessionInline]

    fieldsets = (
        ("Identity & Status", {
            "fields": ("id", "display_name", "profile_completion_status", "archived_at"),
        }),
        ("Professional Context", {
            "fields": ("profession", "company_name", "industry", "department", "responsibilities"),
        }),
        ("Contact (Restricted)", {
            "classes": ("collapse",),
            "fields": ("email", "phone"),
        }),
        ("Audit & Security", {
            "classes": ("collapse",),
            "fields": ("access_token_hash", "token_created_at", "token_revoked_at", "created_at", "updated_at"),
        }),
    )

@admin.register(VisitorConsent)
class VisitorConsentAdmin(admin.ModelAdmin):
    list_display = [
        "visitor",
        "category",
        "status",
        "policy_version",
        "recorded_at",
        "revoked_at",
    ]
    list_filter = [
        "category",
        "status",
        "policy_version",
        "recorded_at",
    ]
    search_fields = ["visitor__id", "visitor__company_name"]
    readonly_fields = ["recorded_at", "revoked_at"]

@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "visitor",
        "status",
        "created_at",
        "last_activity_at",
        "ended_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["id", "visitor__id", "visitor__company_name"]
    readonly_fields = ["id", "created_at", "last_activity_at"]
