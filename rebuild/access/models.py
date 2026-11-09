import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from .policy import ROLES


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=[("store", "Store"), ("warehouse", "Warehouse")], default="store")
    active = models.BooleanField(default=True)


class Role(models.Model):
    # Immutable templates, not user-editable permission lists in R04.
    code = models.CharField(primary_key=True, max_length=40, choices=[(code, code) for code in ROLES])


class RoleAssignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role", "branch"], condition=Q(branch__isnull=False), name="unique_branch_role"),
            models.UniqueConstraint(fields=["user", "role"], condition=Q(branch__isnull=True), name="unique_company_role"),
            models.CheckConstraint(condition=(Q(role_id__in=[k for k, v in ROLES.items() if v.scope == "company"], branch__isnull=True) | Q(role_id__in=[k for k, v in ROLES.items() if v.scope == "branch"], branch__isnull=False)), name="role_scope_matches_branch"),
        ]


class BranchAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "branch"], name="unique_user_branch_access")]


class AccessLock(models.Model):
    """Singleton row serializes membership/ownership mutations per tenant."""
    key = models.PositiveSmallIntegerField(primary_key=True, default=1)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(key=1), name="access_lock_singleton")]


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_id = models.UUIDField(null=True)
    action = models.CharField(max_length=80)
    target_id = models.CharField(max_length=80, blank=True)
    request_id = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    # No arbitrary payload/PII or password metadata accepted.


class ProviderConnection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    provider = models.CharField(max_length=20, default="waseel", choices=[("waseel", "Waseel")])
    environment = models.CharField(max_length=20, choices=[("sandbox", "Sandbox"), ("production", "Production")])
    provider_id = models.CharField(max_length=80)
    secret_ref = models.CharField(max_length=200)  # Reference only, never a token/password.

    class Meta:
        constraints = [models.UniqueConstraint(fields=["branch", "provider", "environment"], name="unique_provider_branch_environment")]
