from django.db import connection
from django_tenants.utils import tenant_context
from directory.models import Company
from .authorization import require


def run_authorized(company_id, actor_id, action, operation, branch_ids=()):
    """Internal task boundary; operation/action must come from trusted server code.

    Queue authentication/signatures and actual task dispatch belong to R13.
    ORM instances and client-selected callbacks must never be queued.
    """
    connection.set_schema_to_public()
    company = Company.objects.get(pk=company_id, state=Company.State.READY)
    with tenant_context(company):
        require(actor_id, action, branch_ids)
        return operation()
