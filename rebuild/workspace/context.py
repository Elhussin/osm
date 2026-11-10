from django.conf import settings
from access.authorization import authorization_state
from access.models import Branch
from access.policy import permits, ResourceScope, BRANCH_ACTIONS


def ui_context(request):
    company = getattr(request, "company", None)
    result = {"is_signed_in": False, "company_name": company.name if company else "نظام البصريات", "smtp_ready": settings.INVITE_DELIVERY == "smtp"}
    if company is None or not request.user.is_authenticated:
        return result
    state = authorization_state(request.user.pk)
    if state is None:
        return result
    principal, context, grants = state
    flags = {name: permits(principal, context, action, ResourceScope(context.company_id), grants) for name, action in {
        "can_members": "members.manage", "can_roles": "roles.manage", "can_branches": "branches.manage", "can_audit": "audit.read", "can_ownership": "ownership.transfer", "can_catalog": "catalog.read", "can_catalog_manage": "catalog.manage", "can_fiscal": "company.manage",
    }.items()}
    branch_ids = [pk for pk in context.active_branches if any(permits(principal, context, action, ResourceScope(context.company_id, frozenset([pk])), grants) for action in BRANCH_ACTIONS | {"provider.configure"})]
    result["can_customers"] = any(permits(principal, context, "customer.read", ResourceScope(context.company_id, frozenset([pk])), grants) for pk in branch_ids)
    result["can_inventory"] = flags["can_catalog"] and any(permits(principal, context, "stock.read", ResourceScope(context.company_id, frozenset([pk])), grants) for pk in branch_ids)
    branches = list(Branch.objects.filter(pk__in=branch_ids).order_by("code"))
    selected = next((b for b in branches if str(b.pk) == request.session.get("selected_branch")), None)
    result.update(flags, is_signed_in=True, user_branches=branches, selected_branch=selected)
    return result
