from django.db import connection
from .views import live, ready


class HealthMiddleware:
    """Infrastructure probes contain no tenant identity and never load a session."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path not in {"/health/live/", "/health/ready/"}:
            return self.get_response(request)
        request.get_host()  # Enforce ALLOWED_HOSTS even without tenant middleware.
        connection.set_schema_to_public()
        return live(request) if request.path == "/health/live/" else ready(request)
