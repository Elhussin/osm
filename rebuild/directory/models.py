import uuid
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Company(TenantMixin):
    class State(models.TextChoices):
        INITIALIZING = "initializing"
        READY = "ready"
        FAILED = "failed"
        SUSPENDED = "suspended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    state = models.CharField(max_length=20, choices=State.choices, default=State.INITIALIZING)
    created_at = models.DateTimeField(auto_now_add=True)
    provision_key = models.UUIDField(unique=True, null=True, editable=False)
    requested_domain = models.CharField(max_length=253, unique=True, null=True, editable=False)
    auto_create_schema = False
    auto_drop_schema = False


class CompanyDomain(DomainMixin):
    pass
