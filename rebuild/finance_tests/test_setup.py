from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import date
from unittest.mock import patch
import uuid
from psycopg import sql
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError, DatabaseError
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TransactionTestCase, override_settings
from django_tenants.utils import tenant_context
from access.models import AuditEvent
from access.services import create_member, assign_role, revoke_role
from directory.db_roles import grant_tenant_runtime
from finance.models import Account, AccountingPeriod, SetupOperation
from finance.setup_services import create_account, change_account, create_period, change_period
from finance.services import save_fiscal_profile
from finance_tests.test_fiscal import data
from workspace_tests import test_workspace as fixtures


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccountingSetupTests(TransactionTestCase):
    setUp = fixtures.WorkspaceTests.setUp
    login = fixtures.WorkspaceTests.login
    get = fixtures.WorkspaceTests.get
    post = fixtures.WorkspaceTests.post

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def account(self, **changes):
        values = dict(code="1000", name="Synthetic assets", kind="asset", normal_side="debit", is_group=True, operation_key=uuid.uuid4(), reason="Synthetic account")
        values.update(changes)
        return create_account(self.owner.pk, **values)

    def period(self, **changes):
        values = dict(code="2026-11", name="Synthetic November", starts_on="2026-11-01", ends_on="2026-11-30", operation_key=uuid.uuid4(), reason="Synthetic period")
        values.update(changes)
        return create_period(self.owner.pk, **values)

    def account_change(self, account, action="disable", **changes):
        account.refresh_from_db()
        values = dict(account_id=account.pk, action=action, expected_version=account.version, operation_key=uuid.uuid4(), reason="Synthetic change")
        values.update(changes)
        return change_account(self.owner.pk, **values)

    def period_change(self, period, action="close", **changes):
        period.refresh_from_db()
        values = dict(period_id=period.pk, action=action, expected_version=period.version, operation_key=uuid.uuid4(), reason="Synthetic period change")
        values.update(changes)
        return change_period(self.owner.pk, **values)

    def test_tree_classification_contra_side_fixed_paths_and_depth_limit(self):
        with tenant_context(self.a):
            root = self.account(code=" a-100 ").account
            self.assertEqual((root.code, root.path, root.depth), ("A-100", "A-100", 1))
            leaf = self.account(code="1010", parent_id=root.pk, is_group=False, normal_side="credit").account
            self.assertEqual((leaf.path, leaf.normal_side), ("A-100/1010", "credit"))
            for changes in ({"code": "A-100"}, {"code": "BAD/CODE"}, {"kind": "other"}, {"normal_side": "other"}, {"is_group": "yes"}, {"parent_id": leaf.pk}, {"parent_id": root.pk, "kind": "expense"}):
                with self.subTest(changes=changes), self.assertRaises(ValidationError):
                    self.account(**changes)
            current = root
            for level in range(2, 9):
                current = self.account(code="G" + str(level), parent_id=current.pk).account
            with self.assertRaises(ValidationError):
                self.account(code="G9", parent_id=current.pk)

    def test_rename_and_state_preserve_operation_snapshots_and_reject_stale(self):
        with tenant_context(self.a):
            original = self.account()
            account = original.account
            changed = self.account_change(account, "rename", name="New synthetic name")
            self.assertEqual((changed.before["name"], changed.after["name"]), ("Synthetic assets", "New synthetic name"))
            original.refresh_from_db()
            self.assertEqual(original.after["name"], "Synthetic assets")
            with self.assertRaises(ValidationError):
                self.account_change(account, expected_version=1)
            with self.assertRaises(ValidationError):
                self.account_change(account, "rename", name="New synthetic name")
            self.account_change(account)
            with self.assertRaises(ValidationError):
                self.account_change(account)
            self.account_change(account, "activate")
            account.refresh_from_db()
            self.assertEqual((account.active, account.version, account.operations.count()), (True, 4, 4))

    def test_parent_disable_and_child_activation_do_not_leave_active_orphans(self):
        with tenant_context(self.a):
            root = self.account().account
            leaf = self.account(code="1010", parent_id=root.pk, is_group=False).account
            with self.assertRaises(ValidationError):
                self.account_change(root)
            self.account_change(leaf)
            self.account_change(root)
            with self.assertRaises(ValidationError):
                self.account(code="1020", parent_id=root.pk)
            with self.assertRaises(ValidationError):
                self.account_change(leaf, "activate")
            self.account_change(root, "activate")
            self.account_change(leaf, "activate")

    def test_period_bounds_overlap_closed_periods_and_adjacency(self):
        with tenant_context(self.a):
            first = self.period().period
            self.period_change(first)
            for start, end in [("2026-10-01", "2026-11-01"), ("2026-11-30", "2026-12-05"), ("2026-11-15", "2026-11-15"), ("2026-10-01", "2026-12-31")]:
                with self.subTest(start=start, end=end), self.assertRaises(ValidationError):
                    self.period(code="X", starts_on=start, ends_on=end)
            self.period(code="PREV", starts_on="2026-10-01", ends_on="2026-10-31")
            self.period(code="NEXT", starts_on="2026-12-01", ends_on="2026-12-31")
            self.period(code="DAY", starts_on="2027-01-01", ends_on="2027-01-01")
            for changes in ({"starts_on": "invalid"}, {"starts_on": "2026-12-01", "ends_on": "2026-11-01"}, {"starts_on": True}):
                with self.assertRaises(ValidationError):
                    self.period(code="BAD", **changes)

    def test_period_close_reopen_version_and_history(self):
        with tenant_context(self.a):
            period = self.period().period
            key = uuid.uuid4()
            closed = self.period_change(period, operation_key=key)
            self.assertEqual(self.period_change(period, operation_key=key, expected_version=1).pk, closed.pk)
            with self.assertRaises(ValidationError):
                self.period_change(period, operation_key=key, expected_version=1, reason="Changed replay")
            self.assertEqual((closed.before["state"], closed.after["state"]), ("open", "closed"))
            with self.assertRaises(ValidationError):
                self.period_change(period)
            with self.assertRaises(ValidationError):
                self.period_change(period, "reopen", expected_version=1)
            self.period_change(period, "reopen")
            period.refresh_from_db()
            self.assertEqual((period.state, period.version, period.starts_on, period.operations.count()), ("open", 3, date(2026, 11, 1), 3))

    def test_replays_and_revoked_accountant_and_admin_flags(self):
        with tenant_context(self.a):
            accountant = create_member(self.owner.pk, username="accountant", password=fixtures.PASSWORD)
            grant = assign_role(self.owner.pk, user_id=accountant.pk, role_code="accountant")
            values = dict(code="CASH", name="Synthetic cash", kind="asset", normal_side="debit", is_group=False, operation_key=uuid.uuid4(), reason="Accountant setup")
            first = create_account(accountant.pk, **values)
            self.assertEqual(create_account(accountant.pk, **values).pk, first.pk)
            with self.assertRaises(ValidationError):
                create_account(accountant.pk, **(values | {"name": "Changed"}))
            key = uuid.uuid4()
            period_op = self.period(operation_key=key)
            self.assertEqual(self.period(operation_key=key).pk, period_op.pk)
            with self.assertRaises(ValidationError):
                self.period(operation_key=key, ends_on="2026-11-29")
            change_values = dict(account_id=first.account_id, action="disable", expected_version=1, operation_key=uuid.uuid4(), reason="Disable")
            changed = change_account(accountant.pk, **change_values)
            self.assertEqual(changed.pk, change_account(accountant.pk, **change_values).pk)
            period_values = dict(period_id=period_op.period_id, action="close", expected_version=1, operation_key=uuid.uuid4(), reason="Accountant close")
            closed = change_period(accountant.pk, **period_values)
            self.assertEqual(change_period(accountant.pk, **period_values).pk, closed.pk)
            revoke_role(self.owner.pk, assignment_id=grant.pk)
            accountant.is_superuser = True
            accountant.save(update_fields=["is_superuser"])
            for call in (lambda: create_account(accountant.pk, **values), lambda: change_account(accountant.pk, **change_values), lambda: change_period(accountant.pk, **period_values), lambda: create_period(accountant.pk, code="P", name="P", starts_on="2027-01-01", ends_on="2027-01-31", operation_key=uuid.uuid4(), reason="Denied")):
                with self.assertRaises(PermissionDenied):
                    call()

    def test_rollback_of_creation_changes_periods_and_audit(self):
        with tenant_context(self.a):
            with patch("finance.setup_services.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.account()
            self.assertFalse(Account.objects.exists())
            self.assertFalse(SetupOperation.objects.exists())
            account = self.account().account
            with patch("finance.setup_services.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.account_change(account)
            account.refresh_from_db()
            self.assertEqual((account.active, account.version, account.operations.count()), (True, 1, 1))
            with patch("finance.setup_services.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.period()
            self.assertFalse(AccountingPeriod.objects.exists())
            period = self.period().period
            with patch("finance.setup_services.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.period_change(period)
            period.refresh_from_db()
            self.assertEqual((period.state, period.version, period.operations.count()), ("open", 1, 1))
            self.assertEqual(AuditEvent.objects.filter(action__startswith="finance.").count(), 2)

    def parallel(self, calls):
        barrier = Barrier(2)
        def execute(call):
            connections.close_all()
            try:
                barrier.wait(timeout=15)
                with tenant_context(self.a):
                    return call().pk
            except ValidationError:
                return None
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(execute, calls))

    def test_concurrent_code_and_key_create_one_account(self):
        results = self.parallel([lambda: self.account()] * 2)
        self.assertEqual(sum(value is not None for value in results), 1)
        key = uuid.uuid4()
        results = self.parallel([lambda: self.account(code="2000", operation_key=key)] * 2)
        self.assertIsNotNone(results[0])
        self.assertEqual(results[0], results[1])

    def test_concurrent_overlap_and_expected_version(self):
        results = self.parallel([lambda: self.period(code="A"), lambda: self.period(code="B", starts_on="2026-11-15", ends_on="2026-12-15")])
        self.assertEqual(sum(value is not None for value in results), 1)
        with tenant_context(self.a):
            period = AccountingPeriod.objects.get()
        values = dict(period_id=period.pk, action="close", expected_version=1, reason="Concurrent close")
        results = self.parallel([lambda: change_period(self.owner.pk, operation_key=uuid.uuid4(), **values)] * 2)
        self.assertEqual(sum(value is not None for value in results), 1)

    def test_http_scopes_choices_permissions_forged_identity_and_csrf(self):
        with tenant_context(self.a):
            account = self.account().account
            period = self.period().period
            admin = create_member(self.owner.pk, username="admin", password=fixtures.PASSWORD)
            assign_role(self.owner.pk, user_id=admin.pk, role_code="company_admin")
        for username in ("cashier", "admin"):
            self.login(username)
            for path in ("/finance/accounts/", "/finance/accounts/new/", "/finance/periods/", f"/finance/accounts/{account.pk}/"):
                self.assertEqual(self.get(path).status_code, 403)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r05.test")
        for path in (f"/finance/accounts/{account.pk}/", f"/finance/periods/{period.pk}/"):
            self.assertEqual(foreign.get(path, HTTP_HOST="b.r05.test").status_code, 404)
        self.assertEqual(foreign.get("/finance/accounts/", HTTP_HOST="b.r05.test").context["page_obj"].paginator.count, 0)
        with tenant_context(self.b):
            owner_b = get_user_model().objects.get(username="owner")
            with self.assertRaises(ValidationError):
                create_account(owner_b.pk, code="CHILD", name="Cross company", kind="asset", normal_side="debit", is_group=False, parent_id=account.pk, operation_key=uuid.uuid4(), reason="Denied")
            with self.assertRaises(ValidationError):
                change_period(owner_b.pk, period_id=period.pk, action="close", expected_version=1, operation_key=uuid.uuid4(), reason="Denied")
        self.login()
        form_new = self.get("/finance/accounts/new/").context["form"]
        create_values = {"code": "1010", "name": "HTTP child", "kind": "asset", "normal_side": "debit", "structure": "posting", "parent_id": str(account.pk), "operation_key": form_new.initial["operation_key"], "reason": "HTTP child"}
        self.assertEqual(self.post("/finance/accounts/new/", create_values).status_code, 422)
        create_values["parent_id"] = " 1000 "
        self.assertEqual(self.post("/finance/accounts/new/", create_values).status_code, 302)
        with tenant_context(self.a):
            self.assertEqual(Account.objects.get(code="1010").parent_id, account.pk)
        strict = Client(enforce_csrf_checks=True)
        strict.cookies = self.client.cookies
        self.assertEqual(strict.post("/finance/accounts/new/", {}, HTTP_HOST="a.r05.test").status_code, 403)
        response = self.get(f"/finance/accounts/{account.pk}/")
        form = response.context["form"]
        payload = {"action": "rename", "name": "HTTP name", "expected_version": 1, "operation_key": form.initial["operation_key"], "reason": "HTTP rename", "code": "FORGED", "kind": "expense", "is_group": False}
        self.assertEqual(self.post(f"/finance/accounts/{account.pk}/", payload).status_code, 302)
        with tenant_context(self.a):
            account.refresh_from_db()
            self.assertEqual((account.code, account.kind, account.is_group, account.name), ("1000", "asset", True, "HTTP name"))
        self.assertEqual(self.post(f"/finance/accounts/{account.pk}/", payload | {"operation_key": uuid.uuid4()}).status_code, 422)
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            for table in ("finance_account", "finance_accountingperiod", "finance_setupoperation"):
                cursor.execute("SELECT to_regclass(%s)", ["public." + table])
                self.assertIsNone(cursor.fetchone()[0])

    def test_postgres_constraints_and_runtime_immutable_identity(self):
        role = "r09_setup_" + uuid.uuid4().hex
        with tenant_context(self.a):
            account = self.account().account
            period = self.period().period
            for values in ({"kind": "wrong"}, {"normal_side": "wrong"}, {"version": 0}, {"depth": 9}, {"parent_id": account.pk, "depth": 2}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Account.objects.filter(pk=account.pk).update(**values)
            with self.assertRaises(IntegrityError), transaction.atomic():
                AccountingPeriod.objects.create(code="OVERLAP", name="Overlap", starts_on="2026-11-30", ends_on="2026-12-01", created_by=self.owner)
            with self.assertRaises(IntegrityError), transaction.atomic():
                AccountingPeriod.objects.filter(pk=period.pk).update(state="other")
            with self.assertRaises(DatabaseError), transaction.atomic():
                AccountingPeriod.objects.create(code="BAD", name="Bad", starts_on="2027-02-02", ends_on="2027-02-01", created_by=self.owner)
            with self.assertRaises(IntegrityError), transaction.atomic():
                SetupOperation.objects.create(kind="account_created", period=period, after={}, reason="Wrong target", operation_key=uuid.uuid4(), payload_digest="0" * 64, created_by=self.owner)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='finance_accountingperiod'::regclass AND conname='finance_period_no_overlap'")
                definition = cursor.fetchone()[0]
                self.assertIn("EXCLUDE USING gist", definition)
                self.assertIn("&&", definition)
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    self.account(code="RUNTIME")
                    self.account_change(account, "rename", name="Runtime name")
                    self.account_change(account)
                    self.account_change(account, "activate")
                    self.period_change(period)
                    self.period_change(period, "reopen")
                    self.period(code="RUNTIME-P", starts_on="2026-12-01", ends_on="2026-12-31")
                statements = ["UPDATE finance_account SET code=code WHERE false", "UPDATE finance_account SET parent_id=parent_id WHERE false", "UPDATE finance_account SET normal_side=normal_side WHERE false", "DELETE FROM finance_account WHERE false", "UPDATE finance_accountingperiod SET starts_on=starts_on WHERE false", "UPDATE finance_accountingperiod SET name=name WHERE false", "DELETE FROM finance_accountingperiod WHERE false", "UPDATE finance_setupoperation SET reason=reason WHERE false", "DELETE FROM finance_setupoperation WHERE false"]
                for statement in statements:
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_migration_preserves_existing_fiscal_revision(self):
        with tenant_context(self.a):
            revision = save_fiscal_profile(self.owner.pk, data=data(), expected_version=0, operation_key=uuid.uuid4(), reason="Synthetic existing fiscal profile")
            MigrationExecutor(connection).migrate([("finance", "0001_initial")])
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes("finance"))
            revision.refresh_from_db()
            self.assertEqual((revision.version, revision.legal_name), (1, "Synthetic fiscal seller"))
            self.assertFalse(Account.objects.exists())
