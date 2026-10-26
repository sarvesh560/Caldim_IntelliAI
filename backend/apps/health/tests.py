from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.conf import settings

class HealthCheckEndpointTests(TestCase):
    """
    Test suite for GET /api/v1/health/ endpoint.
    """

    def setUp(self):
        self.client = APIClient()
        self.health_url = reverse("system_health")

    def test_health_check_returns_http_200(self):
        """Health check endpoint should return HTTP 200 OK."""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_payload_structure(self):
        """Health check should return safe system status information."""
        response = self.client.get(self.health_url)
        data = response.json()

        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("service", data)
        self.assertEqual(data["service"], "caldim-intellisolve-api")
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
        self.assertIn("environment", data)

    def test_health_check_does_not_leak_secrets_or_env(self):
        """Ensure no secrets, passwords, or internal variables are exposed in payload."""
        response = self.client.get(self.health_url)
        data = response.json()
        raw_text = response.content.decode("utf-8")

        # Must not contain secret key or database password
        self.assertNotIn(settings.SECRET_KEY, raw_text)
        self.assertNotIn("password", raw_text.lower())
        self.assertNotIn("secret", raw_text.lower())
        self.assertNotIn("token", raw_text.lower())
        self.assertNotIn("database", raw_text.lower())

    def test_health_check_disallows_unsafe_methods(self):
        """POST, PUT, DELETE methods should not be allowed on the health check endpoint."""
        post_response = self.client.post(self.health_url, {})
        self.assertEqual(post_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        put_response = self.client.put(self.health_url, {})
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        delete_response = self.client.delete(self.health_url)
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
