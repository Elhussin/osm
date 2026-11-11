from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import uuid
from psycopg import sql
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TransactionTestCase, override_settings
from django_tenants.utils import tenant_context
from access.services import create_branch, create_member, assign_role, revoke_role, grant_branch_access, revoke_branch_access
from access.models import AuditEvent, Branch
from directory.db_roles import grant_tenant_runtime
from finance.models import Account, JournalEntry, JournalLine
from finance.setup_services import create_account, change_account, create_period
from sales.models import CashRegister, RegisterOperation
from sales.registers import create_register, change_register, registers_for
from workspace_tests import test_workspace as fixtures


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CashRegisterTests(TransactionTestCase):
    login = fixtures.WorkspaceTests.login
    get = fixtures.WorkspaceTests.get
    post = fixtures.WorkspaceTests.post

    def setUp(self):
        fixtures.WorkspaceTests.setUp(self)
        with tenant_context(self.a):
            self.other = create_branch(self.owner.pk, code="OTHER", name="Synthetic hidden branch")
            self.cash = self.account("1101")
            self.second_cash = self.account("1102")
            self.admin = create_member(self.owner.pk, username="register-admin", password=fixtures.PASSWORD)
            self.admin_grant = assign_role(self.owner.pk, user_id=self.admin.pk, role_code="company_admin")
            self.ledger_grant = assign_role(self.owner.pk, user_id=self.admin.pk, role_code="accountant")
            grant_branch_access(self.owner.pk, user_id=self.admin.pk, branch_id=self.branch.pk)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def account(self, code, **changes):
        values = dict(code=code, name="Synthetic cash " + code, kind="asset", normal_side="debit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic chart")
        values.update(changes)
        return create_account(self.owner.pk, **values).account

    def create(self, **changes):
        values = dict(branch_id=self.branch.pk, code="POS-1", name="Synthetic register", cash_account_code=self.cash.code, operation_key=uuid.uuid4(), reason="Synthetic setup")
        actor = changes.pop("actor_id", self.owner.pk)
        values.update(changes)
        return create_register(actor, **values)

    def change(self, register, **changes):
        register.refresh_from_db()
        values = dict(register_id=register.pk, action="rename", name="Renamed register", expected_version=register.version, operation_key=uuid.uuid4(), reason="Synthetic change")
        actor = changes.pop("actor_id", self.owner.pk)
        values.update(changes)
        if values["action"] != "rename":
            values.pop("name", None)
        return change_register(actor, **values)

    def test_normalized_identity_dedicated_accounts_and_immutable_snapshots(self):
        with tenant_context(self.a):
            created = self.create(code=" pos-1 ")
            register = created.register
            self.assertEqual((register.code, register.currency, register.version), ("POS-1", "SAR", 1))
            renamed = self.change(register)
            self.change(register, action="disable")
            self.change(register, action="activate")
            created.refresh_from_db()
            self.assertEqual(created.after["name"], "Synthetic register")
            self.assertEqual((renamed.before["version"], renamed.after["version"]), (1, 2))
            self.assertEqual(register.operations.count(), 4)
            self.assertEqual(AuditEvent.objects.filter(action__startswith="sales.register.").count(), 4)
            self.assertEqual((JournalEntry.objects.count(), JournalLine.objects.count()), (0, 0))
            with self.assertRaises(ValidationError):
                self.create(cash_account_code=self.second_cash.code)
            with self.assertRaises(ValidationError):
                self.create(code="POS-2")
            second = self.create(branch_id=self.other.pk, cash_account_code=self.second_cash.code).register
            self.assertEqual(second.code, register.code)

    def test_invalid_cash_classification_group_inactive_and_ancestor(self):
        with tenant_context(self.a):
            group = self.account("1000", is_group=True)
            contra = self.account("1103", normal_side="credit")
            expense = self.account("5001", kind="expense")
            child = self.account("1104", parent_id=group.pk)
            change_account(self.owner.pk, account_id=self.cash.pk, action="disable", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic disable")
            for code in ("MISSING", group.code, contra.code, expense.code, self.cash.code):
                with self.subTest(code=code), self.assertRaises(ValidationError):
                    self.create(cash_account_code=code)
            # Synthetic recovery inconsistency: the service must still reject a disabled ancestor.
            Account.objects.filter(pk=group.pk).update(active=False)
            with self.assertRaises(ValidationError):
                self.create(cash_account_code=child.code)
            self.assertEqual(CashRegister.objects.count(), 0)

    def test_activation_rechecks_account_and_disabled_register_does_not_release_mapping(self):
        with tenant_context(self.a):
            register = self.create().register
            self.change(register, action="disable")
            change_account(self.owner.pk, account_id=self.cash.pk, action="disable", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic disable")
            self.change(register)
            with self.assertRaises(ValidationError):
                self.change(register, action="activate")
            with self.assertRaises(ValidationError):
                self.create(code="OTHER-POS")
            register.refresh_from_db()
            self.assertFalse(register.active)

    def test_idempotency_payload_conflict_stale_version_and_invalid_actions(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            first = self.create(operation_key=key)
            self.assertEqual(self.create(operation_key=key).pk, first.pk)
            with self.assertRaises(ValidationError):
                self.create(operation_key=key, name="Changed payload")
            change_key = uuid.uuid4()
            values = dict(register_id=first.register_id, action="rename", name="New name", expected_version=1, operation_key=change_key, reason="Synthetic rename")
            changed = change_register(self.owner.pk, **values)
            self.assertEqual(change_register(self.owner.pk, **values).pk, changed.pk)
            with self.assertRaises(ValidationError):
                change_register(self.owner.pk, **(values | {"operation_key": uuid.uuid4()}))
            for action in ("delete", [], None):
                with self.assertRaises(ValidationError):
                    change_register(self.owner.pk, register_id=first.register_id, action=action, expected_version=2, operation_key=uuid.uuid4(), reason="Synthetic invalid")
            for code in ("", "bad_code", "عربي", "X" * 31):
                with self.assertRaises(ValidationError):
                    self.create(code=code)

    def test_composed_roles_branch_scope_and_reauthorization_on_replay(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            record = self.create(actor_id=self.admin.pk, operation_key=key)
            hidden = self.create(branch_id=self.other.pk, cash_account_code=self.second_cash.code).register
            self.assertEqual(list(registers_for(self.admin.pk).values_list("pk", flat=True)), [record.register_id])
            with self.assertRaises(ValidationError):
                self.change(hidden, actor_id=self.admin.pk)
            revoke_branch_access(self.owner.pk, user_id=self.admin.pk, branch_id=self.branch.pk)
            with self.assertRaises(PermissionDenied):
                self.create(actor_id=self.admin.pk, operation_key=key)
            grant_branch_access(self.owner.pk, user_id=self.admin.pk, branch_id=self.branch.pk)
            revoke_role(self.owner.pk, assignment_id=self.admin_grant.pk)
            self.admin.is_superuser = True
            self.admin.save(update_fields=["is_superuser"])
            with self.assertRaises(PermissionDenied):
                self.create(actor_id=self.admin.pk, operation_key=key)
            with self.assertRaises(PermissionDenied):
                registers_for(self.admin.pk)

    def test_failure_rolls_back_configuration_operation_and_audit(self):
        with tenant_context(self.a):
            before = AuditEvent.objects.count()
            with patch("sales.registers.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.create()
            self.assertFalse(CashRegister.objects.exists())
            self.assertFalse(RegisterOperation.objects.exists())
            self.assertEqual(AuditEvent.objects.count(), before)
            register = self.create().register
            with patch("sales.registers.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.change(register)
            register.refresh_from_db()
            self.assertEqual((register.name, register.version, register.operations.count()), ("Synthetic register", 1, 1))

    def parallel(self, calls):
        barrier = Barrier(2)
        def run(call):
            connections.close_all()
            try:
                with tenant_context(self.a):
                    barrier.wait(timeout=15)
                    return call().pk
            except ValidationError:
                return None
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, calls))

    def test_concurrent_duplicate_keys_and_competing_identity(self):
        key = uuid.uuid4()
        results = self.parallel([lambda: self.create(operation_key=key)] * 2)
        self.assertIsNotNone(results[0])
        self.assertEqual(results[0], results[1])
        with tenant_context(self.a):
            register = CashRegister.objects.get()
            values = dict(register_id=register.pk, action="rename", expected_version=1, reason="Synthetic race")
        results = self.parallel([lambda: change_register(self.owner.pk, name="Name A", operation_key=uuid.uuid4(), **values), lambda: change_register(self.owner.pk, name="Name B", operation_key=uuid.uuid4(), **values)])
        self.assertEqual(sum(row is not None for row in results), 1)

    def test_concurrent_dedicated_account_cannot_be_shared(self):
        results = self.parallel([lambda: self.create(code="POS-A"), lambda: self.create(code="POS-B")])
        self.assertEqual(sum(row is not None for row in results), 1)
        with tenant_context(self.a):
            self.assertEqual((CashRegister.objects.count(), RegisterOperation.objects.count()), (1, 1))

    def test_http_scopes_choices_search_csrf_and_forged_identity(self):
        with tenant_context(self.a):
            visible = self.create(actor_id=self.admin.pk).register
            hidden = self.create(branch_id=self.other.pk, cash_account_code=self.second_cash.code, name="Hidden register").register
        self.login("register-admin")
        response = self.get("/sales/registers/")
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertNotContains(response, "Hidden register")
        self.assertEqual(self.get("/sales/registers/", {"q": "Hidden"}).context["page_obj"].paginator.count, 0)
        self.assertEqual(self.get(f"/sales/registers/{hidden.pk}/").status_code, 404)
        form = self.get("/sales/registers/new/")
        self.assertContains(form, f'value="{self.branch.pk}"')
        self.assertNotContains(form, f'value="{self.other.pk}"')
        strict = Client(enforce_csrf_checks=True)
        strict.cookies = self.client.cookies
        self.assertEqual(strict.post("/sales/registers/new/", {}, HTTP_HOST="a.r05.test").status_code, 403)
        payload = dict(action="rename", name="Safe rename", reason="Synthetic HTTP", expected_version=1, operation_key=str(uuid.uuid4()), branch_id=str(self.other.pk), cash_account_code=self.second_cash.code, currency="USD", created_by="forged")
        self.assertEqual(self.post(f"/sales/registers/{visible.pk}/", payload).status_code, 302)
        with tenant_context(self.a):
            visible.refresh_from_db()
            self.assertEqual((visible.branch_id, visible.cash_account_id, visible.currency, visible.created_by_id), (self.branch.pk, self.cash.pk, "SAR", self.admin.pk))
        self.assertEqual(self.get("/sales/registers/", {"q": "Safe"}).context["page_obj"].paginator.count, 1)

    def test_other_company_denied_roles_and_inactive_branch(self):
        with tenant_context(self.a):
            register = self.create().register
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r05.test")
        self.assertEqual(foreign.get(f"/sales/registers/{register.pk}/", HTTP_HOST="b.r05.test").status_code, 404)
        self.assertEqual(foreign.get("/sales/registers/", HTTP_HOST="b.r05.test").context["page_obj"].paginator.count, 0)
        self.login("cashier")
        self.assertEqual(self.get("/sales/registers/").status_code, 403)
        self.assertEqual(self.get("/sales/registers/new/").status_code, 403)
        with tenant_context(self.a):
            Branch.objects.filter(pk=self.branch.pk).update(active=False)
            self.assertFalse(registers_for(self.owner.pk).exists())
            with self.assertRaises(PermissionDenied):
                self.create()

    def test_postgresql_constraints_and_runtime_immutable_identity(self):
        role = "r10_register_" + uuid.uuid4().hex
        with tenant_context(self.a):
            register = self.create().register
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashRegister.objects.create(branch=self.branch, code=register.code, name="Duplicate", cash_account=self.second_cash, created_by=self.owner)
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashRegister.objects.create(branch=self.other, code="OTHER", name="Shared cash", cash_account=self.cash, created_by=self.owner)
            for values in (dict(currency="USD"), dict(version=0), dict(code="lowercase")):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    CashRegister.objects.filter(pk=register.pk).update(**values)
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    self.change(register)
                    self.create(code="POS-2", cash_account_code=self.second_cash.code)
                for statement in ("UPDATE sales_cashregister SET code=code WHERE false", "UPDATE sales_cashregister SET branch_id=branch_id WHERE false", "UPDATE sales_cashregister SET cash_account_id=cash_account_id WHERE false", "UPDATE sales_cashregister SET currency=currency WHERE false", "DELETE FROM sales_cashregister WHERE false", "UPDATE sales_registeroperation SET reason=reason WHERE false", "DELETE FROM sales_registeroperation WHERE false"):
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            for table in ("sales_cashregister", "sales_registeroperation"):
                cursor.execute("SELECT to_regclass(%s)", ["public." + table])
                self.assertIsNone(cursor.fetchone()[0])

    def test_migration_preserves_existing_chart_period_and_ledger_history(self):
        with tenant_context(self.a):
            period = create_period(self.owner.pk, code="2026-11", name="Synthetic period", starts_on="2026-11-01", ends_on="2026-11-30", operation_key=uuid.uuid4(), reason="Synthetic history").period
            from finance.journals import save_journal_draft, act_on_journal_draft
            capital = self.account("3001", kind="equity", normal_side="credit")
            draft = save_journal_draft(self.owner.pk, branch_id=self.branch.pk, entry_date="2026-11-11", description="Synthetic pre-register ledger", lines=[dict(account_code=self.cash.code, debit="5", credit="0"), dict(account_code=capital.code, debit="0", credit="5")], operation_key=uuid.uuid4(), reason="Synthetic draft").draft
            entry = act_on_journal_draft(self.owner.pk, draft_id=draft.pk, action="post", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic posting").entry
            before = (list(Account.objects.order_by("code").values()), list(JournalEntry.objects.values()), list(JournalLine.objects.order_by("position").values()))
            MigrationExecutor(connection).migrate([("sales", None)])
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes("sales"))
            period.refresh_from_db()
            self.assertEqual(before, (list(Account.objects.order_by("code").values()), list(JournalEntry.objects.values()), list(JournalLine.objects.order_by("position").values())))
            self.assertEqual(entry.period_id, period.pk)
            self.assertEqual(CashRegister.objects.count(), 0)
