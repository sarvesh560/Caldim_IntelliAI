from django.urls import path
from .views import (
    VisitorCreateView,
    VisitorDetailView,
    VisitorSessionCreateView,
    VisitorConsentRecordView,
    VisitorTokenRevokeView,
)

urlpatterns = [
    # POST /api/v1/visitors/ -> create profile
    path("", VisitorCreateView.as_view(), name="visitor_create"),
    # GET /api/v1/visitors/{visitor_id}/ -> read own profile (authenticated)
    path("<uuid:visitor_id>/", VisitorDetailView.as_view(), name="visitor_detail"),
    # POST /api/v1/visitors/{visitor_id}/sessions/ -> create consultation session
    path("<uuid:visitor_id>/sessions/", VisitorSessionCreateView.as_view(), name="visitor_session_create"),
    # POST /api/v1/visitors/{visitor_id}/consent/ -> record/update consent
    path("<uuid:visitor_id>/consent/", VisitorConsentRecordView.as_view(), name="visitor_consent_record"),
    # POST /api/v1/visitors/{visitor_id}/revoke-token/ -> revoke access token
    path("<uuid:visitor_id>/revoke-token/", VisitorTokenRevokeView.as_view(), name="visitor_token_revoke"),
]
