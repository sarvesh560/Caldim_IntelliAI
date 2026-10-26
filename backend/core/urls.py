"""
URL configuration for CALDIM IntelliSolve AI backend.

API versioning follows /api/v1/...
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # Versioned API v1 namespace
    path("api/v1/", include([
        path("health/", include("apps.health.urls")),
        path("visitors/", include("apps.visitors.urls")),
        path("products/", include("apps.products.urls")),
        path("consultations/", include("apps.ai_engine.urls")),
        # path("proposals/", include("apps.proposals.urls")),
        # path("analytics/", include("apps.analytics.urls")),
    ])),
]
