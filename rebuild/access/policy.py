"""Company-bound authorization; inputs must be loaded by trusted server adapters.

This module performs no database access and does not prove schema/session isolation.
Resource.branch_ids is the *complete* set of branches required by an operation,
not a client-selected filter. Lists must be scoped before count/pagination in R04.
"""
from dataclasses import dataclass
from types import MappingProxyType


COMPANY_ACTIONS = frozenset({
    "company.manage", "members.manage", "roles.manage", "branches.manage",
    "ownership.transfer", "provider.configure", "catalog.read", "catalog.manage",
    "ledger.read", "ledger.post", "audit.read",
})
BRANCH_ACTIONS = frozenset({
    "customer.read", "customer.write", "prescription.read", "prescription.write",
    "invoice.read", "invoice.create", "invoice.confirm", "payment.read",
    "payment.record", "payment.reverse", "stock.read", "stock.reserve", "stock.issue",
    "stock.transfer", "stock.receive", "stock.reverse", "insurance.read", "insurance.prepare", "insurance.submit",
    "reports.read", "data.export",
})
ALL_ACTIONS = COMPANY_ACTIONS | BRANCH_ACTIONS


@dataclass(frozen=True)
class Role:
    scope: str
    permissions: frozenset[str]


ROLES = MappingProxyType({
    "owner": Role("company", ALL_ACTIONS),
    "company_admin": Role("company", frozenset({"company.manage", "members.manage", "roles.manage", "branches.manage", "audit.read"})),
    "catalog_reader": Role("company", frozenset({"catalog.read"})),
    "accountant": Role("company", frozenset({"invoice.read", "payment.read", "payment.record", "payment.reverse", "ledger.read", "ledger.post", "reports.read", "data.export"})),
    "integration_admin": Role("company", frozenset({"provider.configure"})),
    "branch_manager": Role("branch", frozenset({"customer.read", "customer.write", "invoice.read", "invoice.create", "invoice.confirm", "payment.read", "payment.record", "payment.reverse", "stock.read", "stock.reserve", "stock.issue", "stock.transfer", "stock.receive", "reports.read"})),
    "cashier": Role("branch", frozenset({"customer.read", "customer.write", "invoice.read", "invoice.create", "invoice.confirm", "payment.read", "payment.record"})),
    "optometrist": Role("branch", frozenset({"customer.read", "prescription.read", "prescription.write"})),
    "inventory_clerk": Role("branch", frozenset({"stock.read", "stock.reserve", "stock.issue", "stock.transfer", "stock.receive"})),
    "insurance_officer": Role("branch", frozenset({"customer.read", "prescription.read", "insurance.read", "insurance.prepare", "insurance.submit"})),
})


@dataclass(frozen=True)
class Principal:
    user_id: str
    company_id: str
    branch_access: frozenset[str] = frozenset()
    authenticated: bool = True
    active: bool = True


@dataclass(frozen=True)
class CompanyContext:
    company_id: str
    active_branches: frozenset[str] = frozenset()
    ready: bool = True


@dataclass(frozen=True)
class ResourceScope:
    company_id: str
    branch_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Grant:
    user_id: str
    company_id: str
    role: str
    branch_id: str | None = None
    active: bool = True


def permits(principal: Principal, context: CompanyContext, action: str,
            resource: ResourceScope, grants: tuple[Grant, ...]) -> bool:
    """Default-deny predicate for current server-resolved identity and scope."""
    if not principal.authenticated or not principal.active or not context.ready:
        return False
    if not principal.user_id or not context.company_id:
        return False
    if principal.company_id != context.company_id or resource.company_id != context.company_id:
        return False
    if action not in ALL_ACTIONS:
        return False
    branches = resource.branch_ids
    if action in BRANCH_ACTIONS and not branches:
        return False
    # Even company administrators need explicit access to every targeted branch.
    if not branches <= context.active_branches or not branches <= principal.branch_access:
        return False
    covered = set()
    for grant in grants:
        if not grant.active or grant.user_id != principal.user_id or grant.company_id != context.company_id:
            continue
        role = ROLES.get(grant.role)
        if role is None or action not in role.permissions:
            continue
        if role.scope == "company":
            if grant.branch_id is not None:
                continue  # Malformed assignment cannot convert a company role to branch privilege.
            return True
        if grant.branch_id is None or grant.branch_id not in context.active_branches:
            continue
        if action in COMPANY_ACTIONS:
            continue
        covered.add(grant.branch_id)
    return bool(branches) and branches <= covered
