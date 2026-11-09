import hashlib
import re
import uuid
from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, transaction
from django_tenants.utils import tenant_context

from .models import Company, CompanyDomain


@contextmanager
def domain_lock(domain):
    number = int.from_bytes(hashlib.sha256(domain.encode()).digest()[:8], "big", signed=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(%s)", [number])
    try:
        yield
    finally:
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", [number])


def provision_company(*, name, domain, username, password, operation_key, email="", grant_runtime=True):
    """Deployment-only provisioning. No HTTP route; no credentials printed or stored in public."""
    if connection.schema_name != "public":
        raise ValidationError("Provisioning requires public context")
    domain = domain.strip().lower().rstrip(".")
    if not name.strip() or len(domain) > 253 or not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", domain) or any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") for label in domain.split(".")):
        raise ValidationError("Invalid company domain")
    operation_key = uuid.UUID(str(operation_key))
    candidate = get_user_model()(username=username, email=email)
    validate_password(password, candidate)
    with domain_lock(domain):
        company = Company.objects.filter(provision_key=operation_key).first()
        if company:
            if company.requested_domain != domain:
                raise ValidationError("Provisioning key belongs to a different domain")
            if company.state == Company.State.READY:
                return company  # Retry does not reset credentials or add owners.
            if company.state != Company.State.FAILED:
                raise ValidationError("Company cannot be resumed in this state")
            company.state = Company.State.INITIALIZING
            company.save(update_fields=["state"])
        else:
            if CompanyDomain.objects.filter(domain=domain).exists() or Company.objects.filter(requested_domain=domain).exists():
                raise ValidationError("Company domain is reserved")
            company = Company.objects.create(name=name, schema_name="c_" + uuid.uuid4().hex, provision_key=operation_key, requested_domain=domain)
        try:
            company.create_schema(check_if_exists=True, verbosity=0)
            with tenant_context(company), transaction.atomic():
                from access.seed import seed_access
                from access.models import Branch, BranchAccess, RoleAssignment, AuditEvent
                seed_access()
                event = AuditEvent.objects.filter(action="company.provisioned", target_id=str(company.pk)).first()
                if event:
                    owner = get_user_model().objects.get(pk=event.actor_id)
                    if owner.username != username:
                        raise ValidationError("Retry cannot replace the provisioned owner")
                else:
                    if get_user_model().objects.exists():
                        raise ValidationError("Refusing to adopt existing accounts without a provisioning record")
                    candidate.set_password(password)
                    candidate.full_clean()
                    candidate.save()
                    owner = candidate
                branch, _ = Branch.objects.get_or_create(code="MAIN", defaults={"name": "الفرع الرئيسي"})
                RoleAssignment.objects.update_or_create(user=owner, role_id="owner", branch=None, defaults={"active": True})
                BranchAccess.objects.update_or_create(user=owner, branch=branch, defaults={"active": True})
                if not event:
                    AuditEvent.objects.create(actor_id=owner.pk, action="company.provisioned", target_id=str(company.pk))
            if grant_runtime:
                call_command("configure_runtime_role", schema=company.schema_name, verbosity=0)
            with transaction.atomic():
                CompanyDomain.objects.get_or_create(domain=domain, defaults={"tenant": company, "is_primary": True})
                company.state = Company.State.READY
                company.save(update_fields=["state"])
            return company
        except Exception:
            connection.set_schema_to_public()
            Company.objects.filter(pk=company.pk).update(state=Company.State.FAILED)
            raise
