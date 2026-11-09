import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from django_tenants.utils import tenant_context

from directory.models import Company, CompanyDomain
from directory.provisioning import provision_company
from access.authorization import allowed, visible_branches
from access.models import Branch, BranchAccess, RoleAssignment, Role, AuditEvent
from access.services import create_branch, create_member, assign_role, revoke_role, revoke_branch_access, grant_branch_access, set_branch_active, set_member_active, transfer_ownership, configure_provider
from identity.invitations import invite_member
from identity.links import issue_link, consume_link
from identity.models import PasswordLink
from directory.db_roles import grant_tenant_runtime
from psycopg import sql
from access.tasks import run_authorized

PASSWORD = "Synthetic-Owner-Password-2026!"
NEW_PASSWORD = "Synthetic-Replaced-Password-2026!"


@override_settings(ALLOWED_HOSTS=["a.r04.test", "b.r04.test", "public.r04.test"], SECURE_SSL_REDIRECT=False, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccessTests(TransactionTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        if not connection.settings_dict["NAME"].startswith("test_optics_rebuild_"):
            raise RuntimeError("Dedicated test database required")
        self.key = uuid.uuid4()
        self.a = provision_company(name="Synthetic A", domain="a.r04.test", username="owner", password=PASSWORD, operation_key=self.key, grant_runtime=False)
        self.b = provision_company(name="Synthetic B", domain="b.r04.test", username="owner", password=NEW_PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        with tenant_context(self.a):
            self.owner = get_user_model().objects.get(username="owner")
            self.main = Branch.objects.get(code="MAIN")
            self.other = create_branch(self.owner.pk, code="OTHER", name="Other")
            self.cashier = create_member(self.owner.pk, username="cashier", password=PASSWORD)
            self.grant = assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="cashier", branch_id=self.main.pk)
        self.client_a = Client()

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def login(self, client=None, username="owner", password=PASSWORD, host="a.r04.test"):
        client = client or self.client_a
        response = client.post("/auth/login/", {"username": username, "password": password}, HTTP_HOST=host)
        self.assertEqual(response.status_code, 302)
        return client

    def test_provisioning_retry_does_not_duplicate_or_reset_owner(self):
        again = provision_company(name="Synthetic A", domain="a.r04.test", username="owner", password=NEW_PASSWORD, operation_key=self.key, grant_runtime=False)
        self.assertEqual(again.pk, self.a.pk)
        with tenant_context(self.a):
            self.assertEqual(RoleAssignment.objects.filter(role_id="owner").count(), 1)
            self.assertTrue(get_user_model().objects.get(username="owner").check_password(PASSWORD))
        with self.assertRaises(ValidationError):
            provision_company(name="Duplicate", domain="a.r04.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)

    def test_failed_provisioning_is_not_published_and_can_resume(self):
        key = uuid.uuid4()
        with patch("access.seed.seed_access", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError):
                provision_company(name="Fail", domain="failed.r04.test", username="owner", password=PASSWORD, operation_key=key, grant_runtime=False)
        company = Company.objects.get(provision_key=key)
        self.assertEqual(company.state, Company.State.FAILED)
        self.assertFalse(CompanyDomain.objects.filter(tenant=company).exists())
        recovered = provision_company(name="Fail", domain="failed.r04.test", username="owner", password=PASSWORD, operation_key=key, grant_runtime=False)
        self.assertEqual(recovered.pk, company.pk)
        self.assertEqual(recovered.state, Company.State.READY)

    def test_login_password_cookie_and_identity_do_not_cross_companies(self):
        self.login()
        denied = self.client_a.get("/account/", HTTP_HOST="b.r04.test")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.client_a.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="b.r04.test").status_code, 400)
        self.login(Client(), password=NEW_PASSWORD, host="b.r04.test")

    def test_branch_scope_is_applied_before_count_and_switch(self):
        self.login(username="cashier")
        result = self.client_a.get("/account/branches/", HTTP_HOST="a.r04.test")
        self.assertEqual(result.context["count"], 1)
        self.assertContains(result, str(self.main.pk))
        self.assertNotContains(result, str(self.other.pk))
        self.assertEqual(self.client_a.post("/account/branch/", {"branch_id": str(self.other.pk)}, HTTP_HOST="a.r04.test").status_code, 403)
        self.assertEqual(self.client_a.post("/account/branch/", {"branch_id": "invalid"}, HTTP_HOST="a.r04.test").status_code, 403)
        self.assertEqual(self.client_a.post("/account/branch/", {"branch_id": str(self.main.pk)}, HTTP_HOST="a.r04.test").status_code, 302)

    def test_role_revocation_takes_effect_on_next_http_request(self):
        self.login(username="cashier")
        with tenant_context(self.a):
            revoke_role(self.owner.pk, assignment_id=self.grant.pk)
        self.assertEqual(self.client_a.get("/account/branches/", HTTP_HOST="a.r04.test").context["count"], 0)

    def test_branch_access_revocation_and_disabled_user_are_immediate(self):
        self.login(username="cashier")
        with tenant_context(self.a):
            revoke_branch_access(self.owner.pk, user_id=self.cashier.pk, branch_id=self.main.pk)
        self.assertEqual(self.client_a.get("/account/branches/", HTTP_HOST="a.r04.test").context["count"], 0)
        with tenant_context(self.a):
            set_member_active(self.owner.pk, user_id=self.cashier.pk, active=False)
        self.assertEqual(self.client_a.get("/account/", HTTP_HOST="a.r04.test").status_code, 403)

    def test_admin_cannot_escalate_or_reset_owner(self):
        with tenant_context(self.a):
            admin = create_member(self.owner.pk, username="admin", password=PASSWORD)
            assign_role(self.owner.pk, user_id=admin.pk, role_code="company_admin")
            for role in ("owner", "accountant", "integration_admin"):
                with self.subTest(role=role), self.assertRaises(PermissionDenied):
                    assign_role(admin.pk, user_id=admin.pk, role_code=role)
            with self.assertRaises(PermissionDenied):
                issue_link(admin.pk, self.owner.pk, "reset")
            # There is no mutable role or raw assignment endpoint to bypass service checks.
            self.assertEqual(RoleAssignment.objects.filter(user=admin, role_id="owner").count(), 0)

    def test_owner_can_delegate_company_wide_accounting_and_recover_own_account(self):
        with tenant_context(self.a):
            accountant = create_member(self.owner.pk, username="accounts", password=PASSWORD)
            assign_role(self.owner.pk, user_id=accountant.pk, role_code="accountant")
            self.assertTrue(allowed(accountant.pk, "ledger.post"))
            grant_branch_access(self.owner.pk, user_id=accountant.pk, branch_id=self.main.pk)
            self.assertTrue(allowed(accountant.pk, "invoice.read", [self.main.pk]))
            self.assertFalse(allowed(accountant.pk, "invoice.create", [self.main.pk]))
            token = issue_link(self.owner.pk, self.owner.pk, "reset")
            consume_link(token, "reset", NEW_PASSWORD)
            self.owner.refresh_from_db()
            self.assertTrue(self.owner.check_password(NEW_PASSWORD))

    def test_last_owner_cannot_be_disabled_and_transfer_reauthenticates(self):
        with tenant_context(self.a):
            with self.assertRaises(ValidationError):
                set_member_active(self.owner.pk, user_id=self.owner.pk, active=False)
            with self.assertRaises(PermissionDenied):
                transfer_ownership(self.owner.pk, new_owner_id=self.cashier.pk, password="wrong")
            transfer_ownership(self.owner.pk, new_owner_id=self.cashier.pk, password=PASSWORD)
            self.assertEqual(RoleAssignment.objects.filter(role_id="owner", active=True, user__is_active=True).count(), 1)
            self.assertFalse(allowed(self.owner.pk, "ownership.transfer"))
            self.assertTrue(allowed(self.cashier.pk, "ownership.transfer"))

    def test_concurrent_ownership_transfers_keep_an_owner(self):
        def transfer():
            try:
                with tenant_context(self.a):
                    transfer_ownership(self.owner.pk, new_owner_id=self.cashier.pk, password=PASSWORD)
                return "ok"
            except PermissionDenied:
                return "denied"
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: transfer(), range(2)))
        self.assertEqual(sorted(outcomes), ["denied", "ok"])
        with tenant_context(self.a):
            self.assertEqual(RoleAssignment.objects.filter(role_id="owner", active=True, user__is_active=True).count(), 1)

    def test_invitation_is_bound_to_company_purpose_and_single_use(self):
        with tenant_context(self.a):
            user, token = invite_member(self.owner.pk, username="invited", email="synthetic@example.invalid", role_code="cashier", branch_id=self.main.pk)
            self.assertFalse(user.is_active)
            self.assertFalse(user.has_usable_password())
            with self.assertRaises(PermissionDenied):
                consume_link(token, "reset", NEW_PASSWORD)
        with tenant_context(self.b), self.assertRaises(PermissionDenied):
            consume_link(token, "invite", NEW_PASSWORD)
        with tenant_context(self.a):
            consume_link(token, "invite", NEW_PASSWORD)
            user.refresh_from_db()
            self.assertTrue(user.is_active)
            with self.assertRaises(PermissionDenied):
                consume_link(token, "invite", NEW_PASSWORD)

    def test_expired_link_is_rejected_and_password_reset_invalidates_session(self):
        self.login(username="cashier")
        with tenant_context(self.a):
            token = issue_link(self.owner.pk, self.cashier.pk, "reset")
            PasswordLink.objects.filter(user=self.cashier).update(expires_at=timezone.now())
            with self.assertRaises(PermissionDenied):
                consume_link(token, "reset", NEW_PASSWORD)
            token = issue_link(self.owner.pk, self.cashier.pk, "reset")
            consume_link(token, "reset", NEW_PASSWORD)
        self.assertEqual(self.client_a.get("/account/", HTTP_HOST="a.r04.test").status_code, 403)

    def test_csrf_enforced_for_login_and_logout(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="a.r04.test").status_code, 403)
        response = client.get("/auth/login/", HTTP_HOST="a.r04.test")
        self.assertEqual(response.status_code, 200)
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post("/auth/login/", {"username": "owner", "password": PASSWORD, "csrfmiddlewaretoken": token}, HTTP_HOST="a.r04.test").status_code, 302)
        self.assertEqual(client.post("/auth/logout/", HTTP_HOST="a.r04.test").status_code, 403)
        self.assertEqual(client.get("/auth/logout/", HTTP_HOST="a.r04.test").status_code, 405)

    def test_login_throttling_is_local_and_not_a_user_enumeration(self):
        for _ in range(5):
            response = self.client_a.post("/auth/login/", {"username": "owner", "password": "wrong"}, HTTP_HOST="a.r04.test")
            self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client_a.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="a.r04.test").status_code, 400)
        self.login(Client(), password=NEW_PASSWORD, host="b.r04.test")

    def test_provider_scope_and_no_raw_secrets_in_audit(self):
        with tenant_context(self.a):
            with self.assertRaises(PermissionDenied):
                configure_provider(self.cashier.pk, branch_id=self.main.pk, environment="sandbox", provider_id="synthetic-provider", secret_ref="secret://synthetic")
            configure_provider(self.owner.pk, branch_id=self.main.pk, environment="sandbox", provider_id="synthetic-provider", secret_ref="secret://synthetic")
            with self.assertRaises(ValidationError):
                configure_provider(self.owner.pk, branch_id=self.other.pk, environment="sandbox", provider_id="synthetic-provider", secret_ref="raw-token")
            events = str(list(AuditEvent.objects.values()))
            for value in (PASSWORD, "synthetic-provider", "secret://synthetic", "raw-token"):
                self.assertNotIn(value, events)

    def test_superuser_flags_do_not_grant_erp_access(self):
        with tenant_context(self.a):
            user = create_member(self.owner.pk, username="technical", password=PASSWORD)
            user.is_superuser = user.is_staff = True
            user.save()
            self.assertFalse(allowed(user.pk, "members.manage"))
            self.assertEqual(visible_branches(user.pk).count(), 0)

    def test_scope_constraint_rejects_company_role_at_branch(self):
        with tenant_context(self.a):
            with self.assertRaises(IntegrityError), transaction.atomic():
                RoleAssignment.objects.create(user=self.cashier, role_id="owner", branch=self.main)

    def test_domain_does_not_take_company_or_schema_from_client(self):
        self.login(username="cashier")
        response = self.client_a.get("/account/branches/", {"schema": self.b.schema_name, "company_id": str(self.b.pk)}, HTTP_HOST="a.r04.test", HTTP_X_TENANT=self.b.schema_name)
        self.assertContains(response, str(self.main.pk))
        self.assertEqual(response.context["count"], 1)
        self.assertEqual(connection.schema_name, "public")

    def test_audit_is_append_only_for_runtime_privileges(self):
        role = "r04_probe_" + uuid.uuid4().hex
        with tenant_context(self.a):
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
            try:
                for verb in ("UPDATE", "DELETE"):
                    with self.subTest(verb=verb), self.assertRaises(ProgrammingError) as error, transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                            cursor.execute("UPDATE access_auditevent SET action = action WHERE false" if verb == "UPDATE" else "DELETE FROM access_auditevent WHERE false")
                    self.assertEqual(getattr(error.exception.__cause__, "sqlstate", None), "42501")
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_public_has_no_login_or_admin_even_with_registered_domain(self):
        public = Company.objects.create(schema_name="public", name="Public", state=Company.State.READY)
        CompanyDomain.objects.create(tenant=public, domain="public.r04.test")
        for path in ("/auth/login/", "/admin/"):
            self.assertEqual(Client().get(path, HTTP_HOST="public.r04.test").status_code, 404)

    def test_role_permission_state_not_cached_across_requests(self):
        with tenant_context(self.a):
            self.assertTrue(allowed(self.cashier.pk, "invoice.read", [self.main.pk]))
            set_branch_active(self.owner.pk, branch_id=self.main.pk, active=False)
            self.assertFalse(allowed(self.cashier.pk, "invoice.read", [self.main.pk]))

    def test_secure_cookie_properties(self):
        with override_settings(SESSION_COOKIE_NAME="__Host-erp_session", SESSION_COOKIE_SECURE=True):
            client = self.login(Client())
            cookie = client.cookies["__Host-erp_session"]
            self.assertTrue(cookie["secure"])
            self.assertTrue(cookie["httponly"])
            self.assertEqual(cookie["path"], "/")
            self.assertFalse(cookie["domain"])

    def test_internal_task_rechecks_revoked_access_and_restores_context(self):
        with tenant_context(self.a):
            revoke_role(self.owner.pk, assignment_id=self.grant.pk)
        with self.assertRaises(PermissionDenied):
            run_authorized(self.a.pk, self.cashier.pk, "invoice.read", lambda: None, [self.main.pk])
        self.assertEqual(connection.schema_name, "public")
        with self.assertRaises(ValueError):
            run_authorized(self.a.pk, self.owner.pk, "members.manage", lambda: (_ for _ in ()).throw(ValueError("synthetic")))
        self.assertEqual(connection.schema_name, "public")

    def test_concurrent_http_requests_do_not_share_tenant_or_actor(self):
        def visit(host, password):
            try:
                client = Client()
                self.login(client, password=password, host=host)
                return client.get("/account/", HTTP_HOST=host).content
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(visit, "a.r04.test", PASSWORD)
            b = pool.submit(visit, "b.r04.test", NEW_PASSWORD)
            content_a, content_b = a.result(), b.result()
        self.assertIn(b"Synthetic A", content_a)
        self.assertNotIn(b"Synthetic B", content_a)
        self.assertIn(b"Synthetic B", content_b)
