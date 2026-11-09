from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from .authorization import require, allowed, current_company, require_delegation
from .models import AccessLock, AuditEvent, Branch, BranchAccess, RoleAssignment, ProviderConnection
from .policy import ROLES
from .context import audit_request_id


def audit(actor_id, action, target_id="", request_id=None):
    values = {"actor_id": actor_id, "action": action, "target_id": str(target_id)}
    correlation = request_id or audit_request_id.get()
    if correlation:
        values["request_id"] = correlation
    AuditEvent.objects.create(**values)


def lock_access():
    current_company()
    AccessLock.objects.select_for_update().get(pk=1)


def owner_count():
    return RoleAssignment.objects.filter(role_id="owner", active=True, user__is_active=True).count()


@transaction.atomic
def create_branch(actor_id, *, code, name, kind="store"):
    lock_access()
    require(actor_id, "branches.manage")
    branch = Branch(code=code.strip(), name=name.strip(), kind=kind)
    branch.full_clean()
    branch.save()
    for owner in RoleAssignment.objects.filter(role_id="owner", active=True, user__is_active=True):
        BranchAccess.objects.update_or_create(user_id=owner.user_id, branch=branch, defaults={"active": True})
    audit(actor_id, "branch.created", branch.pk)
    return branch


@transaction.atomic
def create_member(actor_id, *, username, password, email=""):
    lock_access()
    require(actor_id, "members.manage")
    user = get_user_model()(username=username, email=email)
    validate_password(password, user)
    user.set_password(password)
    user.full_clean()
    user.save()
    audit(actor_id, "member.created", user.pk)
    return user


@transaction.atomic
def assign_role(actor_id, *, user_id, role_code, branch_id=None):
    lock_access()
    require(actor_id, "roles.manage")
    role = ROLES.get(role_code)
    if role is None or role_code == "owner":
        raise PermissionDenied
    if (role.scope == "branch") != (branch_id is not None):
        raise ValidationError("Role scope does not match branch")
    branches = [branch_id] if branch_id else []
    target = get_user_model().objects.get(pk=user_id)
    if branch_id:
        Branch.objects.get(pk=branch_id, active=True)
    # Management permission is insufficient: delegation may not widen the actor.
    require_delegation(actor_id, role, branch_id)
    assignment, _ = RoleAssignment.objects.update_or_create(user=target, role_id=role_code, branch_id=branch_id, defaults={"active": True})
    if branch_id:
        BranchAccess.objects.update_or_create(user=target, branch_id=branch_id, defaults={"active": True})
    audit(actor_id, "role.assigned", assignment.pk)
    return assignment


@transaction.atomic
def revoke_role(actor_id, *, assignment_id):
    lock_access()
    require(actor_id, "roles.manage")
    assignment = RoleAssignment.objects.get(pk=assignment_id)
    if assignment.role_id == "owner":
        raise PermissionDenied  # Ownership changes only through transfer_ownership.
    role = ROLES[assignment.role_id]
    require_delegation(actor_id, role, assignment.branch_id)
    assignment.active = False
    assignment.save(update_fields=["active"])
    audit(actor_id, "role.revoked", assignment.pk)


@transaction.atomic
def set_member_active(actor_id, *, user_id, active):
    lock_access()
    require(actor_id, "members.manage")
    target = get_user_model().objects.select_for_update().get(pk=user_id)
    if RoleAssignment.objects.filter(user=target, role_id="owner", active=True).exists():
        require(actor_id, "ownership.transfer")
        if not active and target.is_active and owner_count() <= 1:
            raise ValidationError("Cannot disable the last active owner")
    target.is_active = active
    target.save(update_fields=["is_active"])
    audit(actor_id, "member.activated" if active else "member.disabled", target.pk)


@transaction.atomic
def revoke_branch_access(actor_id, *, user_id, branch_id):
    lock_access()
    require(actor_id, "roles.manage")
    if not allowed(actor_id, "ownership.transfer"):
        raise PermissionDenied  # Initial branch access administration is owner-only.
    BranchAccess.objects.filter(user_id=user_id, branch_id=branch_id).update(active=False)
    audit(actor_id, "branch_access.revoked", user_id)


@transaction.atomic
def grant_branch_access(actor_id, *, user_id, branch_id):
    lock_access()
    require(actor_id, "roles.manage")
    require(actor_id, "ownership.transfer")  # Owner-only in this initial release.
    user = get_user_model().objects.get(pk=user_id)
    branch = Branch.objects.get(pk=branch_id, active=True)
    BranchAccess.objects.update_or_create(user=user, branch=branch, defaults={"active": True})
    audit(actor_id, "branch_access.granted", user.pk)


@transaction.atomic
def set_branch_active(actor_id, *, branch_id, active):
    lock_access()
    require(actor_id, "branches.manage")
    branch = Branch.objects.select_for_update().get(pk=branch_id)
    branch.active = active
    branch.save(update_fields=["active"])
    audit(actor_id, "branch.activated" if active else "branch.disabled", branch.pk)


@transaction.atomic
def transfer_ownership(actor_id, *, new_owner_id, password):
    lock_access()
    require(actor_id, "ownership.transfer")
    actor = get_user_model().objects.select_for_update().get(pk=actor_id, is_active=True)
    target = get_user_model().objects.select_for_update().get(pk=new_owner_id, is_active=True)
    if actor.pk == target.pk or not actor.check_password(password):
        raise PermissionDenied
    RoleAssignment.objects.update_or_create(user=target, role_id="owner", branch=None, defaults={"active": True})
    for branch in Branch.objects.filter(active=True):
        BranchAccess.objects.update_or_create(user=target, branch=branch, defaults={"active": True})
    RoleAssignment.objects.filter(user=actor, role_id="owner", active=True).update(active=False)
    audit(actor_id, "ownership.transferred", target.pk)


@transaction.atomic
def configure_provider(actor_id, *, branch_id, environment, provider_id, secret_ref):
    lock_access()
    require(actor_id, "provider.configure", [branch_id])
    if not secret_ref.startswith("secret://"):
        raise ValidationError("Only a secret reference is accepted")
    instance = ProviderConnection(branch_id=branch_id, environment=environment, provider_id=provider_id, secret_ref=secret_ref)
    instance.full_clean()
    instance.save()
    audit(actor_id, "provider.configured", instance.pk)
    return instance
