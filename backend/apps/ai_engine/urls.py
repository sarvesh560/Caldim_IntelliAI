"""
CALDIM Consultation Engine URL Routing.
"""
from django.urls import path
from apps.ai_engine.views import (
    ConversationListCreateView,
    ConversationDetailView,
    ConversationMessageCreateView,
)

app_name = "ai_engine"

urlpatterns = [
    path("", ConversationListCreateView.as_view(), name="conversation_list_create"),
    path("<uuid:conversation_id>/", ConversationDetailView.as_view(), name="conversation_detail"),
    path("<uuid:conversation_id>/messages/", ConversationMessageCreateView.as_view(), name="message_create"),
]
