from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal, localcontext
from unittest.mock import patch
import uuid
from psycopg import sql
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.test import Client, TransactionTestCase, override_settings
from django.db.migrations.executor import MigrationExecutor
from django_tenants.utils import tenant_context
from access.models import RoleAssignment, AuditEvent
from access.services import create_member, assign_role, revoke_role, revoke_branch_access, set_member_active
from directory.db_roles import grant_tenant_runtime
from finance.models import JournalEntry, JournalLine
from finance.setup_services import change_account
from sales.models import CashShift, ShiftEvent, CashRegister
from sales.shifts import open_shift, act_on_shift, shifts_for
from sales_tests import test_registers as fixtures


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ShiftWorkflowTests(TransactionTestCase):
    account = fixtures.CashRegisterTests.account
    create = fixtures.CashRegisterTests.create
    change = fixtures.CashRegisterTests.change
    login = fixtures.CashRegisterTests.login
    get = fixtures.CashRegisterTests.get
    post = fixtures.CashRegisterTests.post

    def setUp(self):
        fixtures.CashRegisterTests.setUp(self)
        with tenant_context(self.a):
            self.register = self.create().register
            self.receiver = create_member(self.owner.pk, username="receiver", password=fixtures.fixtures.PASSWORD)
            assign_role(self.owner.pk, user_id=self.receiver.pk, role_code="cashier", branch_id=self.branch.pk)
            self.outsider = create_member(self.owner.pk, username="outsider", password=fixtures.fixtures.PASSWORD)
            assign_role(self.owner.pk, user_id=self.outsider.pk, role_code="cashier", branch_id=self.other.pk)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def open(self, **changes):
        values = dict(register_id=self.register.pk, opening_cash="100", operation_key=uuid.uuid4(), reason="Synthetic custody")
        actor = changes.pop("actor_id", self.cashier.pk)
        values.update(changes)
        return open_shift(actor, **values)

    def act(self, shift, action, **changes):
        shift.refresh_from_db()
        values = dict(shift_id=shift.pk, action=action, expected_version=shift.version, operation_key=uuid.uuid4(), reason="Synthetic shift operation")
        if action in {"request_handover", "accept_handover", "submit_count"}:
            values["counted_cash"] = "100"
        if action == "request_handover":
            values["recipient_username"] = self.receiver.username
        actor = changes.pop("actor_id", self.cashier.pk)
        values.update(changes)
        return act_on_shift(actor, **values)

    def test_open_handover_requires_receiver_acceptance_then_close_preserves_history(self):
        with tenant_context(self.a):
            opened = self.open()
            shift = opened.shift
            self.change(self.register, name="Later register name")
            self.assertEqual(shift.register_snapshot["name"], "Synthetic register")
            request = self.act(shift, "request_handover")
            shift.refresh_from_db()
            self.assertEqual((shift.custodian_id, shift.pending_to_id), (self.cashier.pk, self.receiver.pk))
            with self.assertRaises(PermissionDenied):
                self.act(shift, "accept_handover", actor_id=self.owner.pk)
            with self.assertRaises(ValidationError):
                self.act(shift, "accept_handover", actor_id=self.receiver.pk, counted_cash="99")
            self.act(shift, "accept_handover", actor_id=self.receiver.pk)
            with self.assertRaises(PermissionDenied):
                self.act(shift, "submit_count")
            self.act(shift, "submit_count", actor_id=self.receiver.pk)
            shift.refresh_from_db()
            self.assertEqual((shift.state, shift.custodian_id, shift.version, shift.difference), ("closed", self.receiver.pk, 4, 0))
            opened.refresh_from_db()
            self.assertEqual(opened.after["custodian_id"], str(self.cashier.pk))
            self.assertEqual(request.after["pending_to_id"], str(self.receiver.pk))
            self.assertEqual((shift.events.count(), JournalEntry.objects.count(), JournalLine.objects.count()), (4, 0, 0))
            self.assertEqual(AuditEvent.objects.filter(action__startswith="sales.shift.").count(), 4)
            self.assertNotEqual(self.open().shift_id, shift.pk)

    def test_handover_cancel_reject_and_replayed_request_do_not_reassign_custody(self):
        with tenant_context(self.a):
            shift = self.open().shift
            key = uuid.uuid4()
            request = self.act(shift, "request_handover", operation_key=key)
            self.act(shift, "reject_handover", actor_id=self.receiver.pk)
            replay = act_on_shift(self.cashier.pk, shift_id=shift.pk, action="request_handover", expected_version=1, operation_key=key, reason="Synthetic shift operation", counted_cash="100", recipient_username=self.receiver.username)
            self.assertEqual(replay.pk, request.pk)
            shift.refresh_from_db()
            self.assertIsNone(shift.pending_to_id)
            self.act(shift, "request_handover")
            self.act(shift, "cancel_handover")
            shift.refresh_from_db()
            self.assertEqual(shift.custodian_id, self.cashier.pk)
            self.assertIsNone(shift.pending_to_id)

    def test_variance_requires_explicit_supervisor_approval_and_frozen_count(self):
        with tenant_context(self.a):
            shift = self.open().shift
            count = self.act(shift, "submit_count", counted_cash="95.50")
            shift.refresh_from_db()
            self.assertEqual((shift.state, shift.expected_cash, shift.counted_cash, shift.difference), ("review", Decimal("100"), Decimal("95.50"), Decimal("-4.50")))
            with self.assertRaises(PermissionDenied):
                self.act(shift, "approve_variance")
            for action in ("submit_count", "request_handover"):
                with self.assertRaises(ValidationError):
                    self.act(shift, action)
            with self.assertRaises(ValidationError):
                self.open()
            approved = self.act(shift, "approve_variance", actor_id=self.owner.pk)
            shift.refresh_from_db()
            self.assertEqual((shift.state, shift.difference, count.after["counted_cash"], approved.after["difference"]), ("closed", Decimal("-4.50"), "95.50", "-4.50"))
            with self.assertRaises(ValidationError):
                self.act(shift, "submit_count", actor_id=self.owner.pk)

    def test_zero_and_maximum_money_and_low_global_decimal_precision(self):
        with tenant_context(self.a):
            zero = self.open(opening_cash="0").shift
            self.act(zero, "submit_count", counted_cash="0")
            large = self.open(opening_cash="9999999999999999.99").shift
            with localcontext() as ctx:
                ctx.prec = 2
                event = self.act(large, "submit_count", counted_cash="9999999999999999.98")
            self.assertEqual(event.after["difference"], "-0.01")
            self.act(large, "approve_variance", actor_id=self.owner.pk)
            for value in (1.2, "-1", "NaN", "0.001", "10000000000000000", True):
                with self.subTest(value=value), self.assertRaises(ValidationError):
                    self.open(opening_cash=value)

    def test_pending_handover_blocks_count_and_register_disabling(self):
        with tenant_context(self.a):
            shift = self.open().shift
            for recipient in (self.cashier.username, self.outsider.username, "missing"):
                with self.assertRaises(ValidationError):
                    self.act(shift, "request_handover", recipient_username=recipient)
            with self.assertRaises(ValidationError):
                self.act(shift, "request_handover", counted_cash="101")
            self.act(shift, "request_handover")
            for call in (lambda: self.act(shift, "submit_count"), lambda: self.change(self.register, action="disable")):
                with self.assertRaises(ValidationError):
                    call()
            self.act(shift, "cancel_handover")
            self.act(shift, "submit_count")
            self.change(self.register, action="disable")

    def test_supervisor_recovery_of_disabled_holders_custody_without_impersonation(self):
        with tenant_context(self.a):
            shift = self.open().shift
            self.act(shift, "request_handover")
            set_member_active(self.owner.pk, user_id=self.cashier.pk, active=False)
            cancelled = self.act(shift, "cancel_handover", actor_id=self.owner.pk)
            count = self.act(shift, "submit_count", actor_id=self.owner.pk, counted_cash="102")
            self.act(shift, "approve_variance", actor_id=self.owner.pk)
            self.assertEqual((cancelled.created_by_id, count.created_by_id, count.after["custodian_id"]), (self.owner.pk, self.owner.pk, str(self.cashier.pk)))

    def test_register_and_cash_account_rechecked_for_open_and_accept(self):
        with tenant_context(self.a):
            self.change(self.register, action="disable")
            with self.assertRaises(ValidationError):
                self.open()
            self.change(self.register, action="activate")
            shift = self.open().shift
            self.act(shift, "request_handover")
            change_account(self.owner.pk, account_id=self.cash.pk, action="disable", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic disable")
            with self.assertRaises(ValidationError):
                self.act(shift, "accept_handover", actor_id=self.receiver.pk)
            # Counts can close old custody even if its chart account was disabled.
            self.act(shift, "cancel_handover")
            self.act(shift, "submit_count")
            with self.assertRaises(ValidationError):
                self.open()

    def test_live_permission_revocation_even_for_replay_and_superuser(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            self.open(operation_key=key)
            self.assertEqual(ShiftEvent.objects.count(), 1)
            revoke_branch_access(self.owner.pk, user_id=self.cashier.pk, branch_id=self.branch.pk)
            with self.assertRaises((ValidationError, PermissionDenied)):
                self.open(operation_key=key)
            self.cashier.is_superuser = True
            self.cashier.save(update_fields=["is_superuser"])
            assignment = RoleAssignment.objects.get(user=self.cashier, role_id="cashier", active=True)
            revoke_role(self.owner.pk, assignment_id=assignment.pk)
            with self.assertRaises((ValidationError, PermissionDenied)):
                self.open(operation_key=key)

    def test_idempotent_open_actions_payload_mismatch_and_stale_version(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            first = self.open(operation_key=key)
            self.assertEqual(self.open(operation_key=key).pk, first.pk)
            with self.assertRaises(ValidationError):
                self.open(operation_key=key, opening_cash="101")
            action_key = uuid.uuid4()
            event = self.act(first.shift, "submit_count", operation_key=action_key)
            kwargs = dict(shift_id=first.shift_id, action="submit_count", expected_version=1, operation_key=action_key, reason="Synthetic shift operation", counted_cash="100")
            self.assertEqual(act_on_shift(self.cashier.pk, **kwargs).pk, event.pk)
            with self.assertRaises(ValidationError):
                act_on_shift(self.cashier.pk, **(kwargs | {"counted_cash": "99"}))
            with self.assertRaises(ValidationError):
                act_on_shift(self.cashier.pk, **(kwargs | {"operation_key": uuid.uuid4()}))

    def test_recipient_permissions_are_rechecked_at_acceptance(self):
        with tenant_context(self.a):
            shift = self.open().shift
            self.act(shift, "request_handover")
            assignment = RoleAssignment.objects.get(user=self.receiver, role_id="cashier", active=True)
            revoke_role(self.owner.pk, assignment_id=assignment.pk)
            with self.assertRaises((PermissionDenied, ValidationError)):
                self.act(shift, "accept_handover", actor_id=self.receiver.pk)
            shift.refresh_from_db()
            self.assertEqual((shift.custodian_id, shift.pending_to_id, shift.events.count()), (self.cashier.pk, self.receiver.pk, 2))
            self.act(shift, "cancel_handover")

    def test_failure_rolls_back_head_event_and_audit(self):
        with tenant_context(self.a):
            for target in ("sales.shifts.audit", "sales.shifts.ShiftEvent.objects.create"):
                with patch(target, side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                    self.open()
                self.assertFalse(CashShift.objects.exists())
                self.assertFalse(ShiftEvent.objects.exists())
            shift = self.open().shift
            with patch("sales.shifts.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.act(shift, "submit_count")
            shift.refresh_from_db()
            self.assertEqual((shift.state, shift.version, shift.events.count()), ("open", 1, 1))

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

    def test_concurrent_open_same_key_and_different_keys(self):
        key = uuid.uuid4()
        result = self.parallel([lambda: self.open(operation_key=key)] * 2)
        self.assertIsNotNone(result[0])
        self.assertEqual(result[0], result[1])
        with tenant_context(self.a):
            self.act(CashShift.objects.get(), "submit_count")
        result = self.parallel([lambda: self.open()] * 2)
        self.assertEqual(sum(row is not None for row in result), 1)

    def test_concurrent_accept_cancel_has_one_custody_transition(self):
        with tenant_context(self.a):
            shift = self.open().shift
            self.act(shift, "request_handover")
        values = dict(shift_id=shift.pk, expected_version=2, reason="Synthetic race")
        result = self.parallel([lambda: act_on_shift(self.receiver.pk, action="accept_handover", counted_cash="100", operation_key=uuid.uuid4(), **values), lambda: act_on_shift(self.cashier.pk, action="cancel_handover", operation_key=uuid.uuid4(), **values)])
        self.assertEqual(sum(row is not None for row in result), 1)
        with tenant_context(self.a):
            shift.refresh_from_db()
            self.assertEqual((shift.version, shift.pending_to_id, shift.events.count()), (3, None, 3))
            self.assertIn(shift.custodian_id, (self.cashier.pk, self.receiver.pk))

    def test_concurrent_open_disable_and_close_handover(self):
        result = self.parallel([lambda: self.open(), lambda: self.change(self.register, action="disable")])
        self.assertEqual(sum(row is not None for row in result), 1)
        with tenant_context(self.a):
            self.register.refresh_from_db()
            if not self.register.active:
                self.assertFalse(CashShift.objects.exists())
                self.change(self.register, action="activate")
                shift = self.open().shift
            else:
                shift = CashShift.objects.get()
        values = dict(shift_id=shift.pk, expected_version=1, operation_key=None, reason="Synthetic race", counted_cash="100")
        result = self.parallel([lambda: act_on_shift(self.cashier.pk, action="submit_count", **(values | {"operation_key": uuid.uuid4()})), lambda: act_on_shift(self.cashier.pk, action="request_handover", recipient_username=self.receiver.username, **(values | {"operation_key": uuid.uuid4()}))])
        self.assertEqual(sum(row is not None for row in result), 1)

    def test_postgresql_rejects_head_without_event_wrong_scope_and_closed_mutation(self):
        with tenant_context(self.a):
            base = dict(register=self.register, branch=self.branch, register_snapshot={}, opening_cash="100", custodian=self.cashier, created_by=self.cashier)
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashShift.objects.create(**base)
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashShift.objects.create(**(base | {"branch": self.other}))
            shift = self.open().shift
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashRegister.objects.filter(pk=self.register.pk).update(active=False)
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashShift.objects.filter(pk=shift.pk).update(custodian=self.receiver, version=2)
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashShift.objects.filter(pk=shift.pk).update(pending_to=self.receiver, pending_cash="100", version=2)
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashShift.objects.create(**base)
            self.act(shift, "submit_count", counted_cash="90")
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashShift.objects.filter(pk=shift.pk).update(counted_cash="80", difference="-20", version=3)
            self.act(shift, "approve_variance", actor_id=self.owner.pk)
            with self.assertRaises(IntegrityError), transaction.atomic():
                CashShift.objects.filter(pk=shift.pk).update(version=4)

    def test_restricted_postgresql_runtime_executes_full_flow_and_denies_history_edits(self):
        role = "r10_shifts_" + uuid.uuid4().hex
        with tenant_context(self.a):
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    shift = self.open().shift
                    self.act(shift, "request_handover")
                    self.act(shift, "accept_handover", actor_id=self.receiver.pk)
                    self.act(shift, "submit_count", actor_id=self.receiver.pk, counted_cash="101")
                    self.act(shift, "approve_variance", actor_id=self.owner.pk)
                for statement in ("UPDATE sales_cashshift SET opening_cash=opening_cash WHERE false", "UPDATE sales_cashshift SET branch_id=branch_id WHERE false", "DELETE FROM sales_cashshift WHERE false", "UPDATE sales_shiftevent SET reason=reason WHERE false", "DELETE FROM sales_shiftevent WHERE false"):
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            for name in ("sales_cashshift", "sales_shiftevent"):
                cursor.execute("SELECT to_regclass(%s)", ["public." + name])
                self.assertIsNone(cursor.fetchone()[0])


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ShiftHttpTests(TransactionTestCase):
    setUp = ShiftWorkflowTests.setUp
    account = ShiftWorkflowTests.account
    create = ShiftWorkflowTests.create
    change = ShiftWorkflowTests.change
    login = ShiftWorkflowTests.login
    get = ShiftWorkflowTests.get
    post = ShiftWorkflowTests.post
    open = ShiftWorkflowTests.open
    act = ShiftWorkflowTests.act

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def test_branch_company_filters_form_choices_csrf_and_no_cash_account_leak(self):
        with tenant_context(self.a):
            visible = self.open().shift
            hidden_register = self.create(branch_id=self.other.pk, cash_account_code=self.second_cash.code, name="Hidden cashbox").register
            hidden = self.open(actor_id=self.owner.pk, register_id=hidden_register.pk).shift
        self.login("cashier")
        self.assertEqual(self.get("/sales/shifts/").context["page_obj"].paginator.count, 1)
        self.assertEqual(self.get("/sales/shifts/", {"q": "Hidden"}).context["page_obj"].paginator.count, 0)
        self.assertEqual(self.get(f"/sales/shifts/{hidden.pk}/").status_code, 404)
        form = self.get("/sales/shifts/new/")
        self.assertNotContains(form, "Hidden cashbox")
        self.assertNotContains(form, "Synthetic cash 1101")
        detail = self.get(f"/sales/shifts/{visible.pk}/")
        self.assertNotContains(detail, "Synthetic cash 1101")
        strict = Client(enforce_csrf_checks=True)
        strict.cookies = self.client.cookies
        self.assertEqual(strict.post("/sales/shifts/new/", {}, HTTP_HOST="a.r05.test").status_code, 403)
        self.assertEqual(strict.post(f"/sales/shifts/{visible.pk}/", {}, HTTP_HOST="a.r05.test").status_code, 403)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.fixtures.PASSWORD}, HTTP_HOST="b.r05.test")
        self.assertEqual(foreign.get("/sales/shifts/", HTTP_HOST="b.r05.test").context["page_obj"].paginator.count, 0)
        self.assertEqual(foreign.get(f"/sales/shifts/{visible.pk}/", HTTP_HOST="b.r05.test").status_code, 404)
        self.assertEqual(Client().get("/sales/shifts/", HTTP_HOST="a.r05.test").status_code, 403)

    def test_http_open_is_self_assigned_and_replays_after_occupation_and_close(self):
        self.login("cashier")
        payload = dict(register_id=str(self.register.pk), opening_cash="100", operation_key=str(uuid.uuid4()), reason="Synthetic HTTP open",
            created_by=str(self.owner.pk), custodian_id=str(self.receiver.pk), branch_id=str(self.other.pk), currency="USD")
        response = self.post("/sales/shifts/new/", payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.post("/sales/shifts/new/", payload).status_code, 302)
        with tenant_context(self.a):
            shift = CashShift.objects.get()
            self.assertEqual((shift.created_by_id, shift.custodian_id, shift.branch_id, shift.currency, shift.events.count()), (self.cashier.pk, self.cashier.pk, self.branch.pk, "SAR", 1))
        close = dict(action="submit_count", expected_version=1, operation_key=str(uuid.uuid4()), reason="Synthetic HTTP count", counted_cash="100")
        for _ in range(2):
            self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", close).status_code, 302)
        with tenant_context(self.a):
            self.assertEqual(ShiftEvent.objects.count(), 2)

    def test_http_custody_permissions_rejection_review_and_manager_approval(self):
        with tenant_context(self.a):
            shift = self.open().shift
            self.act(shift, "request_handover")
        self.login()
        accept = dict(action="accept_handover", expected_version=2, operation_key=str(uuid.uuid4()), reason="Synthetic acceptance", counted_cash="100")
        self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", accept).status_code, 403)
        self.login("receiver")
        self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", accept | {"counted_cash": "99"}).status_code, 422)
        self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", accept).status_code, 302)
        self.login("cashier")
        count = dict(action="submit_count", expected_version=3, operation_key=str(uuid.uuid4()), reason="Synthetic count", counted_cash="99")
        self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", count).status_code, 403)
        self.login("receiver")
        self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", count).status_code, 302)
        approve = dict(action="approve_variance", expected_version=4, operation_key=str(uuid.uuid4()), reason="Synthetic review")
        self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", approve).status_code, 403)
        self.login()
        self.assertEqual(self.post(f"/sales/shifts/{shift.pk}/", approve).status_code, 302)
        with tenant_context(self.a):
            shift.refresh_from_db()
            self.assertEqual((shift.state, shift.difference), ("closed", Decimal("-1")))

    def test_additive_shift_migration_preserves_register_configuration(self):
        with tenant_context(self.a):
            before = (list(CashRegister.objects.values()), list(self.register.operations.values()))
            MigrationExecutor(connection).migrate([("sales", "0001_initial")])
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes("sales"))
            self.assertEqual(before, (list(CashRegister.objects.values()), list(self.register.operations.values())))
            self.assertEqual(self.open().shift.register_id, self.register.pk)
