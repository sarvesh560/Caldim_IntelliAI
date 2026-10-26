from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

class HealthCheckView(APIView):
    """
    System health check endpoint.
    
    Returns a simple, safe health status indicating service availability.
    Explicitly does NOT expose credentials, database connection strings,
    environment variables, or internal exception traces.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        payload = {
            "status": "healthy",
            "service": "caldim-intellisolve-api",
            "version": "1.0.0",
            "timestamp": timezone.now().isoformat(),
            "environment": "development" if settings.DEBUG else "production",
        }
        return Response(payload, status=status.HTTP_200_OK)
