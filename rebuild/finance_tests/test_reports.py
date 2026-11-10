from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal, localcontext
import uuid
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from psycopg import sql
from directory.db_roles import grant_tenant_runtime
from django.test import TransactionTestCase, override_settings, Client
from django.test.utils import CaptureQueriesContext
from django_tenants.utils import tenant_context
from access.services import revoke_branch_access, revoke_role
from finance.models import JournalEntry, JournalLine, JournalOperation
from finance.reports import trial_balance, account_ledger
from finance.setup_services import create_account, change_account
from finance_tests import test_journals as fixtures


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class LedgerReportTests(TransactionTestCase):
    setUp = fixtures.JournalTests.setUp
    login = fixtures.JournalTests.login
    get = fixtures.JournalTests.get
    post = fixtures.JournalTests.post
    draft = fixtures.JournalTests.draft
    act = fixtures.JournalTests.act
    reverse = fixtures.JournalTests.reverse

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def trial(self, **changes):
        values = dict(starts_on="2026-11-01", ends_on="2026-12-31")
        values.update(changes)
        return trial_balance(self.accountant.pk, **values)

    def ledger(self, **changes):
        values = dict(account_code="1001", starts_on="2026-11-01", ends_on="2026-12-31")
        values.update(changes)
        return account_ledger(self.accountant.pk, **values)

    def posted(self, **changes):
        return self.act(self.draft(**changes).draft).entry

    def test_ledger_opening_inclusive_dates_and_later_reversal_reference_example(self):
        with tenant_context(self.a):
            expense = create_account(self.owner.pk, code="5001", name="Synthetic expense", kind="expense", normal_side="credit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic chart").account
            self.posted(entry_date="2026-11-01", lines=fixtures.lines("200"))
            original = self.posted(entry_date="2026-11-30", lines=[dict(account_code="5001", debit="30", credit="0"), dict(account_code="1001", debit="0", credit="30")])
            self.reverse(original, entry_date="2026-12-31")
            november = self.ledger(starts_on="2026-11-30", ends_on="2026-11-30")
            self.assertEqual(tuple(november["summary"][key] for key in ("opening", "total_debit", "total_credit", "closing", "movement_count")), (Decimal("200"), 0, Decimal("30"), Decimal("170"), 1))
            quiet = self.ledger(starts_on="2026-11-02", ends_on="2026-11-29")
            self.assertEqual((quiet["summary"]["opening"], quiet["summary"]["closing"], quiet["rows"]), (Decimal("200"), Decimal("200"), []))
            december = self.ledger(starts_on="2026-12-01")
            self.assertEqual((december["summary"]["opening"], december["summary"]["closing"], december["rows"][0]["balance"]), (Decimal("170"), Decimal("200"), Decimal("200")))
            expense_report = self.ledger(account_code=expense.code)
            self.assertEqual([r["balance"] for r in expense_report["rows"]], [Decimal("30"), Decimal("0")])
            report = self.trial()
            row = next(row for row in report["rows"] if row["code"] == "5001")
            self.assertEqual((row["closing"], row["debit"], row["credit"], row["activity"]), (0, Decimal("30"), Decimal("30"), 2))
            self.assertTrue(report["summary"]["balanced"])

    def test_hidden_branch_drafts_and_future_entries_never_enter_totals(self):
        with tenant_context(self.a):
            self.posted(lines=fixtures.lines("12.34"))
            hidden = self.posted(branch_id=self.other.pk, lines=fixtures.lines("9876"))
            self.posted(entry_date="2026-12-01", lines=fixtures.lines("55"))
            self.draft(lines=fixtures.lines("4444"))
            result = self.trial(ends_on="2026-11-30")
            self.assertEqual((result["summary"]["total_debit"], result["summary"]["entry_count"]), (Decimal("12.34"), 1))
            self.assertNotIn(hidden.pk, [row["entry_id"] for row in self.ledger()["rows"]])
            owner = trial_balance(self.owner.pk, starts_on="2026-11-01", ends_on="2026-11-30")
            self.assertEqual(owner["summary"]["total_debit"], Decimal("9888.34"))
            selected = trial_balance(self.owner.pk, starts_on="2026-11-01", ends_on="2026-11-30", branch_id=self.branch.pk)
            self.assertEqual(selected["summary"], result["summary"])

    def test_large_totals_exact_and_independent_of_global_precision(self):
        with tenant_context(self.a):
            for _ in range(2):
                self.posted(lines=fixtures.lines("9999999999999999.99"))
            with localcontext() as ctx:
                ctx.prec = 2
                trial = self.trial()
                ledger = self.ledger()
            expected = Decimal("19999999999999999.98")
            self.assertEqual(trial["summary"]["total_debit"], expected)
            self.assertEqual(trial["summary"]["closing_debit"], expected)
            self.assertTrue(trial["summary"]["balanced"])
            self.assertEqual((ledger["summary"]["closing"], ledger["rows"][-1]["balance"]), (expected, expected))

    def test_inactive_accounts_snapshots_empty_window_and_no_activity(self):
        with tenant_context(self.a):
            original = self.posted()
            change_account(self.owner.pk, account_id=self.cash.pk, action="rename", name="Renamed cash", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic rename")
            change_account(self.owner.pk, account_id=self.cash.pk, action="disable", expected_version=2, operation_key=uuid.uuid4(), reason="Synthetic disable")
            self.reverse(original)
            ledger = self.ledger(starts_on="2026-12-02")
            self.assertFalse(ledger["rows"])
            self.assertEqual(ledger["summary"]["opening"], 0)
            self.assertEqual(ledger["summary"]["closing"], 0)
            row = next(row for row in self.trial()["rows"] if row["code"] == "1001")
            self.assertFalse(row["active"])
            self.assertEqual(row["activity"], 2)
            self.assertEqual(self.ledger()["rows"][0]["account_snapshot"]["name"], "Synthetic cash")
            empty = self.trial(ends_on="2026-11-01")
            self.assertEqual(empty["rows"], [])
            self.assertTrue(empty["summary"]["balanced"])

    def test_pagination_running_balance_and_whole_scope_search_totals(self):
        with tenant_context(self.a):
            for _ in range(21):
                self.posted(lines=fixtures.lines("0.10"))
            first, last = self.ledger(), self.ledger(page=999)
            self.assertEqual((len(first["rows"]), len(last["rows"]), last["page_number"]), (20, 1, 2))
            self.assertEqual((first["rows"][-1]["balance"], last["rows"][0]["balance"]), (Decimal("2.00"), Decimal("2.10")))
            self.assertEqual(last["summary"]["movement_count"], 21)
            self.assertEqual(self.ledger(page="malformed")["page_number"], 1)
        self.login("accountant")
        params = dict(starts_on="2026-11-01", ends_on="2026-12-31", q="1001")
        response = self.get("/finance/reports/trial-balance/", params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(response.context["report"]["summary"]["total_debit"], Decimal("2.10"))

    def test_live_authorization_invalid_branch_dates_account_and_superuser(self):
        with tenant_context(self.a):
            self.posted()
            for branch in (self.other.pk, uuid.uuid4(), "forged"):
                with self.assertRaises(PermissionDenied):
                    self.trial(branch_id=branch)
            for start, end in (("invalid", "2026-12-01"), ("2026-12-02", "2026-11-01")):
                with self.assertRaises(ValidationError):
                    self.trial(starts_on=start, ends_on=end)
            with self.assertRaises(ValidationError):
                self.ledger(account_code="1001' OR 1=1 --")
            revoke_branch_access(self.owner.pk, user_id=self.accountant.pk, branch_id=self.branch.pk)
            self.assertEqual(self.trial()["rows"], [])
            self.assertEqual(self.ledger()["summary"]["movement_count"], 0)
            revoke_role(self.owner.pk, assignment_id=self.grant.pk)
            self.accountant.is_superuser = True
            self.accountant.save(update_fields=["is_superuser"])
            with self.assertRaises(PermissionDenied):
                self.trial()

    def test_http_permissions_company_scope_bad_filters_and_get_only(self):
        with tenant_context(self.a):
            self.posted()
        self.login("accountant")
        params = dict(starts_on="2026-11-01", ends_on="2026-12-31")
        initial = self.get("/finance/reports/ledger/")
        self.assertFalse(initial.context["form"].errors)
        self.assertIsNone(initial.context["report"])
        for path in ("/finance/reports/trial-balance/", "/finance/reports/ledger/"):
            response = self.get(path, params | {"account_code": "1001"})
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, f'value="{self.other.pk}"')
            self.assertEqual(self.post(path).status_code, 405)
            invalid = self.get(path, params | {"branch_id": str(self.other.pk)})
            self.assertIsNone(invalid.context["report"])
            self.assertTrue(invalid.context["form"].errors)
            self.assertIsNone(self.get(path, params | {"ends_on": "bad"}).context["report"])
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.fixtures.PASSWORD}, HTTP_HOST="b.r05.test")
        result = foreign.get("/finance/reports/trial-balance/", params, HTTP_HOST="b.r05.test")
        self.assertEqual(result.context["report"]["summary"]["entry_count"], 0)
        self.login("cashier")
        self.assertEqual(self.get("/finance/reports/trial-balance/").status_code, 403)
        self.assertEqual(self.get("/finance/reports/ledger/").status_code, 403)

    def test_read_only_single_statement_numeric_snapshot_and_no_n_plus_one(self):
        with tenant_context(self.a):
            self.posted()
            before = (JournalEntry.objects.count(), JournalLine.objects.count(), JournalOperation.objects.count())
            with CaptureQueriesContext(connection) as captured:
                self.trial()
                self.ledger()
            queries = [query["sql"].lstrip().upper() for query in captured]
            self.assertEqual(sum(query.startswith("WITH ") for query in queries), 2)
            self.assertFalse(any(query.startswith(("INSERT", "UPDATE", "DELETE", "SELECT FOR UPDATE")) for query in queries))
            self.assertEqual(before, (JournalEntry.objects.count(), JournalLine.objects.count(), JournalOperation.objects.count()))

    def test_reports_execute_with_restricted_postgresql_runtime_grants(self):
        role = "r09_reports_" + uuid.uuid4().hex
        with tenant_context(self.a):
            self.posted()
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    self.assertTrue(self.trial()["summary"]["balanced"])
                    self.assertEqual(self.ledger()["summary"]["closing"], Decimal("100"))
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_concurrent_post_reports_have_complete_balanced_snapshots(self):
        with tenant_context(self.a):
            self.posted()
            draft = self.draft(lines=fixtures.lines("25")).draft
        barrier = Barrier(2)
        def publish():
            connections.close_all()
            try:
                with tenant_context(self.a):
                    barrier.wait(timeout=15)
                    self.act(draft)
            finally:
                connections.close_all()
        def read():
            connections.close_all()
            try:
                with tenant_context(self.a):
                    barrier.wait(timeout=15)
                    return [self.trial()["summary"] for _ in range(8)]
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            post_job, read_job = pool.submit(publish), pool.submit(read)
            post_job.result(timeout=30)
            snapshots = read_job.result(timeout=30)
        for summary in snapshots:
            self.assertTrue(summary["balanced"])
            self.assertIn((summary["entry_count"], summary["total_debit"]), ((1, Decimal("100")), (2, Decimal("125"))))
        with tenant_context(self.a):
            self.assertEqual(self.trial()["summary"]["total_debit"], Decimal("125"))
