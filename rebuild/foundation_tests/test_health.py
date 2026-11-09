from unittest.mock import patch
from django.test import SimpleTestCase, override_settings


@override_settings(ALLOWED_HOSTS=["testserver"], SECURE_SSL_REDIRECT=False)
class HealthTests(SimpleTestCase):
    def test_liveness_needs_no_database_or_company(self):
        response = self.client.get("/health/live/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "alive"})

    def test_readiness_database_failure_is_sanitized(self):
        with patch("config.views.database_ready", side_effect=RuntimeError("private-connection-sentinel")):
            response = self.client.get("/health/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"private-connection-sentinel", response.content)

    def test_unknown_host_is_not_accepted_for_probe(self):
        response = self.client.get("/health/live/", HTTP_HOST="unknown.example")
        self.assertEqual(response.status_code, 400)
