"""R02 policy evidence; PostgreSQL and request adapter checks belong to R04."""
import json
import unittest
from pathlib import Path

from rebuild.access.policy import (
    ALL_ACTIONS, COMPANY_ACTIONS, ROLES, CompanyContext, Grant,
    Principal, ResourceScope, permits,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = json.loads((ROOT / "docs/rebuild/access-matrix.json").read_text(encoding="utf-8"))


def make_case(case):
    principal = Principal(
        case.get("user_id", "user-a"), "company-a",
        frozenset(case.get("branch_access", ["branch-a1"])),
        case.get("authenticated", True), case.get("user_active", True),
    )
    context = CompanyContext(case.get("context_company", "company-a"), frozenset(case.get("active_branches", ["branch-a1", "branch-a2"])), case.get("company_ready", True))
    resource = ResourceScope(case.get("resource_company", "company-a"), frozenset(case.get("branches", ["branch-a1"])))
    grants = []
    for name in case["roles"]:
        role = ROLES.get(name)
        branch = "branch-a1" if role is None or role.scope == "branch" else None
        if case.get("force_branch_assignment"):
            branch = "branch-a1"
        if case.get("force_company_assignment"):
            branch = None
        base = {"user_id": case.get("grant_user", principal.user_id), "company_id": case.get("grant_company", "company-a"), "role": name, "active": case.get("grant_active", True)}
        grants.append(Grant(**base, branch_id=branch))
        for extra in case.get("extra_branch_grants", []):
            grants.append(Grant(**base, branch_id=extra))
    return principal, context, resource, tuple(grants)


class AccessPolicyTests(unittest.TestCase):
    def test_stock_receipt_permissions_are_explicit_and_branch_scoped(self):
        for role in ("inventory_clerk", "branch_manager", "owner"):
            p, context, resource, grants = make_case({"roles": [role]})
            self.assertTrue(permits(p, context, "stock.receive", resource, grants))
            denied = ResourceScope(context.company_id, frozenset(["branch-a2"]))
            self.assertFalse(permits(p, context, "stock.receive", denied, grants))
        for role in ("cashier", "catalog_reader", "company_admin"):
            p, context, resource, grants = make_case({"roles": [role]})
            self.assertFalse(permits(p, context, "stock.receive", resource, grants))

    def test_stock_reversal_is_owner_only_in_current_templates(self):
        for role in ROLES:
            p, context, resource, grants = make_case({"roles": [role]})
            self.assertEqual(role == "owner", permits(p, context, "stock.reverse", resource, grants))

    def test_matrix_integrity(self):
        cases = MATRIX["cases"]
        self.assertEqual("pure_policy_cases_not_database_or_http_isolation_proof", MATRIX["scope"])
        self.assertEqual(40, len(cases))
        self.assertEqual({f"P{i:02d}" for i in range(1, 41)}, {c["id"] for c in cases})
        self.assertTrue(any(c["allow"] for c in cases))
        self.assertTrue(any(not c["allow"] for c in cases))

    def test_role_registry_is_explicit_and_valid(self):
        for role in ROLES.values():
            self.assertIn(role.scope, {"company", "branch"})
            self.assertTrue(role.permissions <= ALL_ACTIONS)
            self.assertNotIn("*", role.permissions)
            if role.scope == "branch":
                self.assertFalse(role.permissions & COMPANY_ACTIONS)

    def test_company_mismatch_denies_every_role_and_action(self):
        # A privilege addition cannot accidentally widen the company boundary.
        for name, role in ROLES.items():
            for action in ALL_ACTIONS:
                principal, context, resource, grants = make_case({"roles": [name]})
                foreign = ResourceScope("company-b", resource.branch_ids)
                with self.subTest(role=name, action=action):
                    self.assertFalse(permits(principal, context, action, foreign, grants))

    def test_evaluation_does_not_reuse_previous_company_or_grants(self):
        p, context, resource, grants = make_case({"roles": ["cashier"]})
        self.assertTrue(permits(p, context, "invoice.read", resource, grants))
        other = CompanyContext("company-b", context.active_branches)
        self.assertFalse(permits(p, other, "invoice.read", ResourceScope("company-b", resource.branch_ids), grants))
        self.assertFalse(permits(p, context, "invoice.read", resource, ()))
        self.assertTrue(permits(p, context, "invoice.read", resource, grants))


def matrix_test(case):
    def test(self):
        principal, context, resource, grants = make_case(case)
        self.assertEqual(case["allow"], permits(principal, context, case["action"], resource, grants), case["name"])
    return test


for _case in MATRIX["cases"]:
    setattr(AccessPolicyTests, f"test_{_case['id']}", matrix_test(_case))


if __name__ == "__main__":
    unittest.main()
