from django.contrib.auth import logout
from django.db import connection
import uuid
from access.context import audit_request_id
from access.authorization import current_company


class BoundSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if connection.schema_name == "public":
            return self.get_response(request)
        company = current_company()
        request.company = company
        if request.user.is_authenticated and request.session.get("company_id") != str(company.pk):
            logout(request)
        token = audit_request_id.set(uuid.uuid4())
        try:
            response = self.get_response(request)
            response["Cache-Control"] = "no-store"
            return response
        finally:
            audit_request_id.reset(token)
