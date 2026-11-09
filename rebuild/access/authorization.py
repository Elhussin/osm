"""Resolve permissions from the current tenant, never from submitted identities."""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import connection
from directory.models import Company
from .models import Branch, BranchAccess, RoleAssignment
from .policy import Principal, CompanyContext, ResourceScope, Grant, permits, ROLES, COMPANY_ACTIONS


def current_company():
    if connection.schema_name == "public":
        raise PermissionDenied
    company = Company.objects.filter(schema_name=connection.schema_name, state=Company.State.READY).first()
    if company is None:
        raise PermissionDenied
    return company


def authorization_state(actor_id):
    company = current_company()
    user = get_user_model().objects.filter(pk=actor_id, is_active=True).first()
    if user is None:
        return None
    company_id = str(company.pk)
    active = frozenset(str(pk) for pk in Branch.objects.filter(active=True).values_list("pk", flat=True))
    access = frozenset(str(pk) for pk in BranchAccess.objects.filter(user=user, active=True, branch__active=True).values_list("branch_id", flat=True))
    grants = tuple(Grant(str(user.pk), company_id, row.role_id, str(row.branch_id) if row.branch_id else None) for row in RoleAssignment.objects.filter(user=user, active=True))
    return Principal(str(user.pk), company_id, access), CompanyContext(company_id, active), grants


def allowed(actor_id, action, branches=()):
    state = authorization_state(actor_id)
    if state is None:
        return False
    principal, context, grants = state
    return permits(principal, context, action, ResourceScope(context.company_id, frozenset(str(pk) for pk in branches)), grants)


def require(actor_id, action, branches=()):
    if not allowed(actor_id, action, branches):
        raise PermissionDenied


def delegation_permitted(state, role, branch_id=None):
    """Pure check shared by server-side choices and mutation authorization."""
    if state is None:
        return False
    principal, context, grants = state
    for permission in role.permissions:
        if role.scope == "company" and permission not in COMPANY_ACTIONS:
            # A company grant can only be delegated by another company grant;
            # checking an empty branch resource would incorrectly deny it.
            if not any(g.branch_id is None and g.role in ROLES and ROLES[g.role].scope == "company" and permission in ROLES[g.role].permissions for g in grants):
                return False
        else:
            branches = frozenset([str(branch_id)]) if branch_id else frozenset()
            if not permits(principal, context, permission, ResourceScope(context.company_id, branches), grants):
                return False
    return True


def require_delegation(actor_id, role, branch_id=None):
    if not delegation_permitted(authorization_state(actor_id), role, branch_id):
        raise PermissionDenied


def visible_branches(actor_id, action="invoice.read"):
    state = authorization_state(actor_id)
    if state is None:
        return Branch.objects.none()
    principal, context, grants = state
    ids = [pk for pk in context.active_branches if permits(principal, context, action, ResourceScope(context.company_id, frozenset([pk])), grants)]
    return Branch.objects.filter(pk__in=ids).order_by("code")
