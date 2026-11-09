from django.db import connection
from django.http import Http404
from django_tenants.middleware.main import TenantMainMiddleware


class CompanyMiddleware(TenantMainMiddleware):
    """No default tenant. Always reset the connection, including exception paths."""
    def get_tenant(self, domain_model, hostname):
        tenant = super().get_tenant(domain_model, hostname)
        if tenant.state != "ready":
            raise Http404("Company unavailable")
        return tenant

    def __call__(self, request):
        try:
            return super().__call__(request)
        finally:
            connection.set_schema_to_public()
