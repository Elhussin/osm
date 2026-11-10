from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal, localcontext
from threading import Barrier
from unittest.mock import patch
import uuid
from psycopg import sql
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.db.migrations.executor import MigrationExecutor
from django.db.models import Sum, F
from django.test import Client, SimpleTestCase, TransactionTestCase, override_settings
from django_tenants.utils import tenant_context
from access.models import AuditEvent
from access.services import create_member, assign_role, create_branch, grant_branch_access, revoke_branch_access, revoke_role
from directory.db_roles import grant_tenant_runtime
from finance.models import Account, AccountingPeriod, JournalDraft, JournalRevision, JournalEntry, JournalLine, JournalCounter, JournalOperation
from finance.journal_money import normalize_lines, amount, MAX_MONEY
from finance.journals import save_journal_draft, act_on_journal_draft, reverse_journal
from finance.setup_services import create_account, change_account, create_period, change_period
from finance.services import save_fiscal_profile
from finance_tests.test_fiscal import data
from workspace_tests import test_workspace as fixtures


def lines(value="100.00", credit=None):
    return [{"account_code": "1001", "debit": value, "credit": "0", "description": "Synthetic debit"},
            {"account_code": "3001", "debit": "0", "credit": credit if credit is not None else value, "description": "Synthetic credit"}]


class JournalMoneyTests(SimpleTestCase):
    def test_exact_totals_independent_of_global_decimal_precision(self):
        with localcontext() as ctx:
            ctx.prec = 2
            rows, debit, credit = normalize_lines(lines("123456789.12"))
            self.assertEqual((debit, credit, rows[0]["debit"]), (Decimal("123456789.12"), Decimal("123456789.12"), "123456789.12"))
        _, debit, credit = normalize_lines([lines("0.10")[0], lines("0.20")[0], lines("0.30")[1]])
        self.assertEqual((debit, credit), (Decimal("0.30"), Decimal("0.30")))

    def test_rejects_float_special_values_excess_precision_and_overflow(self):
        for value in (1.2, True, None, "NaN", "Infinity", "1e3", "-1", "-0.00", "1.001", "00.10", Decimal("NaN"), Decimal("Infinity"), Decimal("0.000"), Decimal("1e99999"), 10 ** 100, "1" * 100):
            with self.subTest(value=str(value)), self.assertRaises(ValidationError):
                amount(value)
        self.assertEqual(amount(str(MAX_MONEY)), MAX_MONEY)
        with self.assertRaises(ValidationError):
            normalize_lines([lines(str(MAX_MONEY))[0]] * 2)

    def test_line_schema_count_and_one_positive_side(self):
        for value in ([], lines() * 21, "json", [dict(account_code="X", debit="1", credit="1")] * 2,
                      [dict(account_code="X", debit="0", credit="0")] * 2, [lines()[0] | {"branch_id": "forged"}, lines()[1]]):
            with self.assertRaises(ValidationError):
                normalize_lines(value)


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class JournalTests(TransactionTestCase):
    login = fixtures.WorkspaceTests.login
    get = fixtures.WorkspaceTests.get
    post = fixtures.WorkspaceTests.post

    def setUp(self):
        fixtures.WorkspaceTests.setUp(self)
        with tenant_context(self.a):
            self.other = create_branch(self.owner.pk, code="OTHER", name="Synthetic other branch")
            self.cash = create_account(self.owner.pk, code="1001", name="Synthetic cash", kind="asset", normal_side="debit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic chart").account
            self.capital = create_account(self.owner.pk, code="3001", name="Synthetic capital", kind="equity", normal_side="credit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic chart").account
            self.period = create_period(self.owner.pk, code="2026-11", name="Synthetic November", starts_on="2026-11-01", ends_on="2026-11-30", operation_key=uuid.uuid4(), reason="Synthetic period").period
            self.next_period = create_period(self.owner.pk, code="2026-12", name="Synthetic December", starts_on="2026-12-01", ends_on="2026-12-31", operation_key=uuid.uuid4(), reason="Synthetic period").period
            self.accountant = create_member(self.owner.pk, username="accountant", password=fixtures.PASSWORD)
            self.grant = assign_role(self.owner.pk, user_id=self.accountant.pk, role_code="accountant")
            grant_branch_access(self.owner.pk, user_id=self.accountant.pk, branch_id=self.branch.pk)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def draft(self, **changes):
        values = dict(branch_id=self.branch.pk, entry_date="2026-11-15", description="Synthetic journal", lines=lines(), operation_key=uuid.uuid4(), reason="Synthetic draft")
        actor = changes.pop("actor_id", self.owner.pk)
        values.update(changes)
        return save_journal_draft(actor, **values)

    def act(self, draft, action="post", **changes):
        draft.refresh_from_db()
        values = dict(draft_id=draft.pk, action=action, expected_version=draft.version, operation_key=uuid.uuid4(), reason="Synthetic action")
        actor = changes.pop("actor_id", self.owner.pk)
        values.update(changes)
        return act_on_journal_draft(actor, **values)

    def reverse(self, entry, **changes):
        values = dict(entry_id=entry.pk, entry_date="2026-12-01", operation_key=uuid.uuid4(), reason="Synthetic reversal")
        actor = changes.pop("actor_id", self.owner.pk)
        values.update(changes)
        return reverse_journal(actor, **values)

    def period_action(self, period, action, **changes):
        period.refresh_from_db()
        values = dict(period_id=period.pk, action=action, expected_version=period.version, operation_key=uuid.uuid4(), reason="Synthetic period action")
        values.update(changes)
        return change_period(self.owner.pk, **values)

    def tally(self):
        for entry in JournalEntry.objects.all():
            sums = entry.lines.aggregate(debit=Sum("debit"), credit=Sum("credit"))
            self.assertEqual((sums["debit"], sums["credit"]), (entry.total_debit, entry.total_credit))
            self.assertEqual(entry.total_debit, entry.total_credit)
            self.assertGreaterEqual(entry.lines.count(), 2)

    def test_unbalanced_revision_then_balanced_posting_and_frozen_account_snapshot(self):
        with tenant_context(self.a):
            draft = self.draft(lines=lines(credit="90.00")).draft
            original = draft.revisions.get()
            with self.assertRaises(ValidationError):
                self.act(draft)
            self.assertFalse(JournalEntry.objects.exists())
            self.assertFalse(JournalCounter.objects.exists())
            self.draft(draft_id=draft.pk, branch_id=None, expected_version=1, lines=lines())
            change_account(self.owner.pk, account_id=self.cash.pk, action="rename", name="Cash at posting", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic rename")
            entry = self.act(draft).entry
            self.assertEqual((entry.number, entry.total_debit, entry.lines.count()), (1, Decimal("100.00"), 2))
            self.assertEqual(entry.lines.get(account=self.cash).account_snapshot["name"], "Cash at posting")
            change_account(self.owner.pk, account_id=self.cash.pk, action="rename", name="Cash later", expected_version=2, operation_key=uuid.uuid4(), reason="Later name")
            self.assertEqual(entry.lines.get(account=self.cash).account_snapshot["name"], "Cash at posting")
            original.refresh_from_db()
            self.assertEqual(original.total_credit, Decimal("90.00"))
            with self.assertRaises(ValidationError):
                self.draft(draft_id=draft.pk, branch_id=None, expected_version=3)
            with self.assertRaises(ValidationError):
                self.act(draft, "cancel")
            self.tally()

    def test_cancel_preserves_revision_and_replay_and_blocks_post(self):
        with tenant_context(self.a):
            draft = self.draft().draft
            key = uuid.uuid4()
            cancelled = self.act(draft, "cancel", operation_key=key)
            self.assertEqual(self.act(draft, "cancel", expected_version=1, operation_key=key).pk, cancelled.pk)
            self.assertEqual(draft.revisions.count(), 1)
            with self.assertRaises(ValidationError):
                self.act(draft)
            with self.assertRaises(ValidationError):
                self.draft(draft_id=draft.pk, branch_id=None, expected_version=2)
            self.assertFalse(JournalEntry.objects.exists())

    def test_post_revalidates_leaf_and_ancestor_activity_and_period(self):
        with tenant_context(self.a):
            draft = self.draft().draft
            change_account(self.owner.pk, account_id=self.cash.pk, action="disable", expected_version=1, operation_key=uuid.uuid4(), reason="Disable")
            with self.assertRaises(ValidationError):
                self.act(draft)
            change_account(self.owner.pk, account_id=self.cash.pk, action="activate", expected_version=2, operation_key=uuid.uuid4(), reason="Activate")
            group = create_account(self.owner.pk, code="G", name="Group", kind="asset", normal_side="debit", is_group=True, operation_key=uuid.uuid4(), reason="Group").account
            bad = lines()
            bad[0]["account_code"] = group.code
            with self.assertRaises(ValidationError):
                self.draft(lines=bad)
            child = create_account(self.owner.pk, code="CHILD", name="Child", kind="asset", normal_side="debit", is_group=False, parent_id=group.pk, operation_key=uuid.uuid4(), reason="Child").account
            rows = lines()
            rows[0]["account_code"] = child.code
            second = self.draft(lines=rows).draft
            Account.objects.filter(pk=group.pk).update(active=False)  # Deployment-role corruption probe, rolled away with test DB.
            with self.assertRaises(ValidationError):
                self.act(second)
            Account.objects.filter(pk=group.pk).update(active=True)
            self.period_action(self.period, "close")
            with self.assertRaises(ValidationError):
                self.act(draft)
            self.period_action(self.period, "reopen")
            self.act(draft)
            self.tally()

    def test_reversal_in_later_period_preserves_disabled_accounts_and_original(self):
        with tenant_context(self.a):
            entry = self.act(self.draft().draft).entry
            before = list(entry.lines.order_by("position").values("account_id", "debit", "credit", "account_snapshot"))
            self.period_action(self.period, "close")
            with self.assertRaises(ValidationError):
                self.reverse(entry, entry_date="2026-11-20")
            with self.assertRaises(ValidationError):
                self.reverse(entry, entry_date="2026-11-01")
            change_account(self.owner.pk, account_id=self.cash.pk, action="disable", expected_version=1, operation_key=uuid.uuid4(), reason="Disable after posting")
            inverse = self.reverse(entry).entry
            self.assertEqual((inverse.number, inverse.period_id, inverse.reverses_id), (2, self.next_period.pk, entry.pk))
            self.assertEqual(list(entry.lines.order_by("position").values("account_id", "debit", "credit", "account_snapshot")), before)
            for old, new in zip(before, inverse.lines.order_by("position")):
                self.assertEqual((new.account_id, new.debit, new.credit, new.account_snapshot), (old["account_id"], old["credit"], old["debit"], old["account_snapshot"]))
            with self.assertRaises(ValidationError):
                self.reverse(entry)
            with self.assertRaises(ValidationError):
                self.reverse(inverse)
            for account in (self.cash, self.capital):
                sums = JournalLine.objects.filter(account=account).aggregate(debit=Sum("debit"), credit=Sum("credit"))
                self.assertEqual(sums["debit"], sums["credit"])
            self.tally()

    def test_idempotency_changed_payload_and_number_reuse_is_rejected(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            op = self.draft(operation_key=key)
            self.assertEqual(self.draft(operation_key=key).pk, op.pk)
            with self.assertRaises(ValidationError):
                self.draft(operation_key=key, lines=lines("99"))
            key = uuid.uuid4()
            post = self.act(op.draft, operation_key=key)
            self.assertEqual(self.act(op.draft, expected_version=1, operation_key=key).pk, post.pk)
            with self.assertRaises(ValidationError):
                self.act(op.draft, expected_version=1, operation_key=key, reason="Changed reason")
            key = uuid.uuid4()
            inverse = self.reverse(post.entry, operation_key=key)
            self.assertEqual(self.reverse(post.entry, operation_key=key).pk, inverse.pk)
            with self.assertRaises(ValidationError):
                self.reverse(post.entry, operation_key=key, entry_date="2026-12-02")
            self.assertEqual((JournalEntry.objects.count(), JournalCounter.objects.get().next_number), (2, 3))

    def test_branch_revocation_role_revocation_and_superuser_do_not_allow_replays(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            draft = self.draft(actor_id=self.accountant.pk, operation_key=key).draft
            post_key = uuid.uuid4()
            post = self.act(draft, actor_id=self.accountant.pk, operation_key=post_key)
            reverse_key = uuid.uuid4()
            self.reverse(post.entry, actor_id=self.accountant.pk, operation_key=reverse_key)
            with self.assertRaises(PermissionDenied):
                self.draft(actor_id=self.accountant.pk, branch_id=self.other.pk)
            revoke_branch_access(self.owner.pk, user_id=self.accountant.pk, branch_id=self.branch.pk)
            for call in (lambda: self.draft(actor_id=self.accountant.pk, operation_key=key), lambda: self.act(draft, actor_id=self.accountant.pk, operation_key=post_key, expected_version=1), lambda: self.reverse(post.entry, actor_id=self.accountant.pk, operation_key=reverse_key)):
                with self.assertRaises((PermissionDenied, ValidationError)):
                    call()
            grant_branch_access(self.owner.pk, user_id=self.accountant.pk, branch_id=self.branch.pk)
            revoke_role(self.owner.pk, assignment_id=self.grant.pk)
            self.accountant.is_superuser = True
            self.accountant.save(update_fields=["is_superuser"])
            with self.assertRaises(PermissionDenied):
                self.draft(actor_id=self.accountant.pk, operation_key=key)

    def test_scoped_http_lists_lookups_revision_branch_choices_and_csrf(self):
        with tenant_context(self.a):
            visible = self.draft().draft
            hidden = self.draft(branch_id=self.other.pk, description="Hidden branch journal").draft
            hidden_entry = self.act(hidden).entry
        self.login("accountant")
        self.assertEqual(self.get("/finance/journals/").context["page_obj"].paginator.count, 1)
        self.assertEqual(self.get("/finance/entries/").context["page_obj"].paginator.count, 0)
        for path in (f"/finance/journals/{hidden.pk}/", f"/finance/journals/{hidden.pk}/revisions/1/", f"/finance/entries/{hidden_entry.pk}/"):
            self.assertEqual(self.get(path).status_code, 404)
        response = self.get("/finance/journals/new/")
        self.assertContains(response, f'value="{self.branch.pk}"')
        self.assertNotContains(response, f'value="{self.other.pk}"')
        strict = Client(enforce_csrf_checks=True)
        strict.cookies = self.client.cookies
        self.assertEqual(strict.post(f"/finance/journals/{visible.pk}/", {}, HTTP_HOST="a.r05.test").status_code, 403)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r05.test")
        self.assertEqual(foreign.get(f"/finance/journals/{visible.pk}/", HTTP_HOST="b.r05.test").status_code, 404)
        self.login("cashier")
        self.assertEqual(self.get("/finance/journals/").status_code, 403)
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            for table in ("finance_journaldraft", "finance_journalrevision", "finance_journalentry", "finance_journalline", "finance_journalcounter", "finance_journaloperation"):
                cursor.execute("SELECT to_regclass(%s)", ["public." + table])
                self.assertIsNone(cursor.fetchone()[0])

    def test_failure_rolls_back_lines_counter_state_operation_and_audit(self):
        with tenant_context(self.a):
            draft = self.draft().draft
            for target in ("finance.journals.JournalLine.objects.bulk_create", "finance.journals.audit"):
                with patch(target, side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                    self.act(draft)
                draft.refresh_from_db()
                self.assertEqual((draft.state, draft.version), ("draft", 1))
                self.assertFalse(JournalEntry.objects.exists())
                self.assertFalse(JournalCounter.objects.exists())
                self.assertEqual(draft.operations.count(), 1)
            entry = self.act(draft).entry
            with patch("finance.journals.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.reverse(entry)
            self.assertEqual((JournalEntry.objects.count(), JournalCounter.objects.get().next_number), (1, 2))
            self.tally()

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

    def test_concurrent_post_same_key_and_different_keys_post_once(self):
        with tenant_context(self.a):
            first, second = self.draft().draft, self.draft().draft
        key = uuid.uuid4()
        values = dict(draft_id=first.pk, action="post", expected_version=1, operation_key=key, reason="Concurrent post")
        results = self.parallel([lambda: act_on_journal_draft(self.owner.pk, **values)] * 2)
        self.assertIsNotNone(results[0])
        self.assertEqual(results[0], results[1])
        values = dict(draft_id=second.pk, action="post", expected_version=1, reason="Different keys")
        results = self.parallel([lambda: act_on_journal_draft(self.owner.pk, operation_key=uuid.uuid4(), **values)] * 2)
        self.assertEqual(sum(value is not None for value in results), 1)
        with tenant_context(self.a):
            self.assertEqual(list(JournalEntry.objects.order_by("number").values_list("number", flat=True)), [1, 2])
            self.tally()

    def test_post_cancel_race_and_concurrent_numbering_and_reverse(self):
        with tenant_context(self.a):
            draft = self.draft().draft
        values = dict(draft_id=draft.pk, expected_version=1, reason="Race state")
        results = self.parallel([lambda: act_on_journal_draft(self.owner.pk, action="post", operation_key=uuid.uuid4(), **values), lambda: act_on_journal_draft(self.owner.pk, action="cancel", operation_key=uuid.uuid4(), **values)])
        self.assertEqual(sum(value is not None for value in results), 1)
        with tenant_context(self.a):
            draft.refresh_from_db()
            self.assertEqual(JournalEntry.objects.filter(draft=draft).exists(), draft.state == "posted")
            a, b = self.draft().draft, self.draft().draft
        results = self.parallel([lambda: act_on_journal_draft(self.owner.pk, draft_id=a.pk, action="post", expected_version=1, operation_key=uuid.uuid4(), reason="Number A"), lambda: act_on_journal_draft(self.owner.pk, draft_id=b.pk, action="post", expected_version=1, operation_key=uuid.uuid4(), reason="Number B")])
        self.assertTrue(all(results))
        with tenant_context(self.a):
            entry = JournalEntry.objects.get(draft=a)
        results = self.parallel([lambda: self.reverse(entry)] * 2)
        self.assertEqual(sum(value is not None for value in results), 1)
        with tenant_context(self.a):
            numbers = list(JournalEntry.objects.order_by("number").values_list("number", flat=True))
            self.assertEqual(numbers, list(range(1, len(numbers) + 1)))
            self.tally()

    def test_period_close_and_post_race_has_no_post_after_close(self):
        with tenant_context(self.a):
            draft = self.draft().draft
        results = self.parallel([lambda: self.period_action(self.period, "close", expected_version=1), lambda: act_on_journal_draft(self.owner.pk, draft_id=draft.pk, action="post", expected_version=1, operation_key=uuid.uuid4(), reason="Race close")])
        self.assertIsNotNone(results[0])
        with tenant_context(self.a):
            self.period.refresh_from_db()
            self.assertEqual(self.period.state, "closed")
            entry = JournalEntry.objects.filter(draft=draft).first()
            if entry:
                self.assertLessEqual(entry.created_at, self.period.operations.get(kind="period_closed").created_at)
            else:
                draft.refresh_from_db()
                self.assertEqual(draft.state, "draft")
            self.tally()

    def test_void_and_draft_creation_race_preserves_reference_guard(self):
        results = self.parallel([lambda: self.period_action(self.period, "void", expected_version=1), lambda: self.draft()])
        self.assertEqual(sum(value is not None for value in results), 1)
        with tenant_context(self.a):
            self.period.refresh_from_db()
            self.assertEqual(self.period.state == "void", not JournalRevision.objects.filter(period=self.period).exists())

    def test_void_unused_period_releases_range_but_referenced_history_blocks_void(self):
        with tenant_context(self.a):
            self.period_action(self.next_period, "close")
            self.period_action(self.next_period, "void")
            with self.assertRaises(ValidationError):
                self.period_action(self.next_period, "reopen")
            with self.assertRaises(IntegrityError), transaction.atomic():
                AccountingPeriod.objects.filter(pk=self.next_period.pk).update(state="open")
            replacement = create_period(self.owner.pk, code="DEC-CORRECTED", name="Corrected December", starts_on="2026-12-01", ends_on="2026-12-31", operation_key=uuid.uuid4(), reason="Correct period").period
            self.assertNotEqual(replacement.pk, self.next_period.pk)
            draft = self.draft().draft
            self.act(draft, "cancel")
            with self.assertRaises(ValidationError):
                self.period_action(self.period, "void")
            with self.assertRaises(IntegrityError), transaction.atomic():
                AccountingPeriod.objects.filter(pk=self.period.pk).update(state="void")

    def test_database_balance_at_commit_and_source_and_line_constraints(self):
        with tenant_context(self.a):
            draft = self.draft().draft
            revision = draft.revisions.get()
            with self.assertRaisesMessage(IntegrityError, "incomplete or unbalanced"), transaction.atomic():
                empty = JournalEntry.objects.create(number=99, branch=self.branch, period=self.period, entry_date=revision.entry_date, draft=draft, revision=revision,
                    description="Empty posted journal", total_debit=100, total_credit=100, created_by=self.owner)
                draft.state, draft.version = "posted", 2
                draft.save(update_fields=["state", "version"])
                JournalOperation.objects.create(draft=draft, entry=empty, kind="journal_posted", draft_version=2, operation_key=uuid.uuid4(), payload_digest="0" * 64, reason="Empty probe", created_by=self.owner)
            draft.refresh_from_db()
            entry = self.act(draft).entry
            with self.assertRaisesMessage(IntegrityError, "incomplete or unbalanced"), transaction.atomic():
                JournalLine.objects.filter(entry=entry, debit__gt=0).update(debit=F("debit") + 1)
            with self.assertRaisesMessage(IntegrityError, "incomplete or unbalanced"), transaction.atomic():
                JournalLine.objects.filter(entry=entry).delete()
            for values in ({"debit": -1}, {"credit": 1}, {"debit": 0}, {"position": 41}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    JournalLine.objects.filter(entry=entry, debit__gt=0).update(**values)
            with self.assertRaises(IntegrityError), transaction.atomic():
                JournalEntry.objects.filter(pk=entry.pk).update(total_credit=99)
            with self.assertRaises(IntegrityError), transaction.atomic():
                JournalOperation.objects.create(draft=draft, kind="draft_cancelled", draft_version=None, operation_key=uuid.uuid4(), payload_digest="0" * 64, reason="Null version probe", created_by=self.owner)
            with connection.cursor() as cursor:
                cursor.execute("SELECT tgdeferrable,tginitdeferred FROM pg_trigger WHERE tgrelid IN ('finance_journalentry'::regclass,'finance_journalline'::regclass) AND tgname IN ('finance_journal_header_balance','finance_journal_line_balance')")
                self.assertEqual(cursor.fetchall(), [(True, True), (True, True)])
            self.tally()

    def test_runtime_executes_complete_posting_and_reversal_but_cannot_mutate_history(self):
        role = "r09_journal_" + uuid.uuid4().hex
        with tenant_context(self.a):
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    entry = self.act(self.draft().draft).entry
                    self.reverse(entry)
                    cancelled = self.act(self.draft().draft, "cancel").draft
                for draft_id in (entry.draft_id, cancelled.pk):
                    with self.assertRaises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute("UPDATE finance_journaldraft SET state='draft',version=version+1 WHERE id=%s", [draft_id])
                for statement in ("UPDATE finance_journalentry SET description=description WHERE false", "DELETE FROM finance_journalentry WHERE false", "UPDATE finance_journalline SET debit=debit WHERE false", "DELETE FROM finance_journalline WHERE false", "UPDATE finance_journalrevision SET description=description WHERE false", "DELETE FROM finance_journalrevision WHERE false", "UPDATE finance_journaloperation SET reason=reason WHERE false", "DELETE FROM finance_journaloperation WHERE false", "UPDATE finance_journaldraft SET branch_id=branch_id WHERE false", "DELETE FROM finance_journaldraft WHERE false", "DELETE FROM finance_journalcounter WHERE false"):
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
                self.tally()
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_migration_preserves_chart_period_and_fiscal_profile_history(self):
        with tenant_context(self.a):
            profile = save_fiscal_profile(self.owner.pk, data=data(), expected_version=0, operation_key=uuid.uuid4(), reason="Existing fiscal profile")
            before = (list(Account.objects.values("id", "code", "name", "version")), list(AccountingPeriod.objects.values("id", "code", "starts_on", "ends_on", "state", "version")))
            MigrationExecutor(connection).migrate([("finance", "0002_account_accountingperiod_setupoperation_and_more")])
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes("finance"))
            profile.refresh_from_db()
            self.assertEqual(profile.version, 1)
            self.assertEqual((list(Account.objects.values("id", "code", "name", "version")), list(AccountingPeriod.objects.values("id", "code", "starts_on", "ends_on", "state", "version"))), before)
            self.assertFalse(JournalDraft.objects.exists())

    def test_http_add_line_preserves_data_without_saving_and_rejects_oversized_formset(self):
        response = self.get("/finance/journals/new/")
        key = response.context["form"].initial["operation_key"]
        values = {"branch_id": str(self.branch.pk), "entry_date": "2026-11-15", "description": "Preserved draft", "reason": "Prepare", "operation_key": key,
            "lines-TOTAL_FORMS": "2", "lines-INITIAL_FORMS": "0", "lines-0-account_code": "1001", "lines-0-debit": "100", "lines-1-account_code": "3001", "lines-1-credit": "100", "command": "add_line"}
        response = self.post("/finance/journals/new/", values)
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.context["lines"].total_form_count(), response.context["form"].initial["description"]), (3, "Preserved draft"))
        with tenant_context(self.a):
            self.assertFalse(JournalDraft.objects.exists())
        self.assertEqual(self.post("/finance/journals/new/", values | {"lines-TOTAL_FORMS": "100000"}).status_code, 400)
