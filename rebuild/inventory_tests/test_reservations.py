from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import uuid
from psycopg import sql
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.test import TransactionTestCase, Client, override_settings
from django_tenants.utils import tenant_context
from access.services import revoke_role
from directory.db_roles import grant_tenant_runtime
from inventory.models import StockBalance, StockReservation, ReservationEvent, StockMovement
from inventory.reservations import reserve_stock, change_reservation
from inventory.reservation_views import ReserveForm
from inventory import services
from inventory_tests import test_matrix as matrix_fixture
PASSWORD = matrix_fixture.PASSWORD


@override_settings(ALLOWED_HOSTS=["a.r08.test", "b.r08.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ReservationTests(TransactionTestCase):
    login = matrix_fixture.MatrixStockTests.login
    get = matrix_fixture.MatrixStockTests.get
    post = matrix_fixture.MatrixStockTests.post
    values = matrix_fixture.MatrixStockTests.values

    def setUp(self):
        matrix_fixture.MatrixStockTests.setUp(self)
        with tenant_context(self.a):
            self.receipt = services.receive_matrix(self.owner.pk, **self.values())

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def reserve(self, **changes):
        values = dict(branch_id=self.main.pk, variant_id=self.template.pk, quantity=5, operation_key=uuid.uuid4(), reason="Synthetic hold", reference="ORDER-TEST")
        values.update(changes)
        return reserve_stock(self.clerk.pk, **values)

    def action(self, event, kind, **changes):
        values = dict(reservation_id=event.reservation_id, kind=kind, expected_version=event.version, operation_key=uuid.uuid4(), reason="Synthetic action")
        values.update(changes)
        return change_reservation(self.owner.pk, **values)

    def assert_balance(self, hand, reserved):
        balance = StockBalance.objects.get()
        self.assertEqual((balance.on_hand, balance.reserved, balance.available), (hand, reserved, hand-reserved))

    def test_partial_issue_release_cancel_and_reverse_preserve_history(self):
        with tenant_context(self.a):
            held = self.reserve()
            self.assert_balance(5, 5)
            issued = self.action(held, "issue", quantity=2)
            self.assert_balance(3, 3)
            released = self.action(issued, "release", quantity=1)
            cancelled = self.action(released, "cancel")
            self.assert_balance(3, 0)
            inverse = self.action(cancelled, "reverse_issue", issue_id=issued.pk)
            self.assert_balance(5, 0)
            reservation = StockReservation.objects.get()
            self.assertEqual((reservation.quantity, reservation.held, reservation.issued, reservation.released, reservation.cancelled), (5, 0, 0, 5, True))
            self.assertEqual(reservation.events.count(), 5)
            self.assertEqual(list(StockMovement.objects.filter(reservation_event__isnull=False).order_by("reservation_event__version").values_list("delta", flat=True)), [-2, 2])
            self.assertEqual(inverse.reverses_id, issued.pk)
            with self.assertRaises(ValidationError):
                self.action(inverse, "reverse_issue", issue_id=issued.pk)
            with self.assertRaises(ValidationError):
                self.action(inverse, "issue", quantity=1)

    def test_replays_and_changed_payloads_and_stale_versions(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            held = self.reserve(operation_key=key)
            self.assertEqual(held.pk, self.reserve(operation_key=key).pk)
            with self.assertRaises(ValidationError):
                self.reserve(operation_key=key, quantity=4)
            issue_key = uuid.uuid4()
            issued = self.action(held, "issue", quantity=1, operation_key=issue_key)
            self.assertEqual(issued.pk, self.action(held, "issue", quantity=1, operation_key=issue_key).pk)
            for kwargs in ({"quantity": 2, "operation_key": issue_key}, {"quantity": 1}):
                with self.assertRaises(ValidationError):
                    self.action(held, "issue", **kwargs)
            self.assert_balance(4, 4)

    def test_invalid_quantities_and_over_reservation_do_not_write(self):
        with tenant_context(self.a):
            for quantity in (0, -1, True, 1.0, "1.5", 6, 1000001):
                with self.subTest(quantity=quantity), self.assertRaises(ValidationError):
                    self.reserve(quantity=quantity)
            self.assertFalse(StockReservation.objects.exists())
            held = self.reserve(quantity=2)
            for kind in ("issue", "release"):
                with self.assertRaises(ValidationError):
                    self.action(held, kind, quantity=3)
            with self.assertRaises(ValidationError):
                self.action(held, "unknown")
            self.assert_balance(5, 2)

    def test_inactive_catalog_blocks_issue_but_allows_release(self):
        with tenant_context(self.a):
            held = self.reserve()
            type(self.template).objects.filter(pk=self.template.pk).update(active=False)
            with self.assertRaises(ValidationError):
                self.action(held, "issue", quantity=1)
            released = self.action(held, "release", quantity=5)
            self.assertEqual(released.released_after, 5)
            self.assert_balance(5, 0)

    def test_receipt_inverse_is_blocked_until_reservation_released(self):
        with tenant_context(self.a):
            held = self.reserve()
            with self.assertRaises(ValidationError):
                services.reverse_receipt(self.owner.pk, receipt_id=self.receipt.pk, operation_key=uuid.uuid4(), reason="Synthetic inverse")
            self.action(held, "cancel")
            services.reverse_receipt(self.owner.pk, receipt_id=self.receipt.pk, operation_key=uuid.uuid4(), reason="Synthetic inverse")
            self.assert_balance(0, 0)

    def test_rollback_after_event_or_physical_movement_failure(self):
        with tenant_context(self.a):
            with patch("inventory.reservations.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.reserve()
            self.assertFalse(StockReservation.objects.exists())
            self.assert_balance(5, 0)
            held = self.reserve()
            with patch("inventory.reservations.StockMovement.objects.create", side_effect=RuntimeError("Synthetic movement failure")), self.assertRaises(RuntimeError):
                self.action(held, "issue", quantity=2)
            self.assert_balance(5, 5)
            self.assertEqual(ReservationEvent.objects.count(), 1)
            self.assertEqual(StockReservation.objects.get().version, 1)

    def test_permissions_rechecked_even_on_replay_and_inverse_owner_only(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            held = self.reserve(operation_key=key)
            issued = change_reservation(self.clerk.pk, reservation_id=held.reservation_id, kind="issue", expected_version=1, quantity=1, operation_key=uuid.uuid4(), reason="Synthetic clerk issue")
            with self.assertRaises(PermissionDenied):
                change_reservation(self.clerk.pk, reservation_id=held.reservation_id, kind="reverse_issue", issue_id=issued.pk, expected_version=2, operation_key=uuid.uuid4(), reason="Synthetic unauthorized inverse")
            revoke_role(self.owner.pk, assignment_id=self.clerk_grant.pk)
            with self.assertRaises(PermissionDenied):
                self.reserve(operation_key=key)
            with self.assertRaises(PermissionDenied):
                self.reserve(branch_id=self.other.pk)
            self.assert_balance(4, 4)

    def test_http_scope_company_and_forged_balance_and_csrf(self):
        with tenant_context(self.a):
            held = self.reserve()
        path = f"/inventory/reservations/{held.reservation_id}/"
        self.assertEqual(self.get(path).status_code, 200)
        self.login("reader")
        self.assertEqual(self.get(path).status_code, 404)
        self.assertEqual(self.get("/inventory/reservations/").status_code, 403)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="b.r08.test")
        self.assertEqual(foreign.get(path, HTTP_HOST="b.r08.test").status_code, 404)
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(path, {}, HTTP_HOST="a.r08.test").status_code, 403)
        self.login("clerk")
        with tenant_context(self.a):
            other_receipt = services.receive_matrix(self.owner.pk, **self.values(branch_id=self.other.pk))
            other_balance = StockBalance.objects.get(branch_id=self.other.pk)
        response = self.post("/inventory/reservations/", {"balance": other_balance.pk, "quantity": 1, "reason": "Forged", "operation_key": uuid.uuid4()})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        with tenant_context(self.a):
            self.assertEqual(StockReservation.objects.count(), 1)

    def parallel(self, operations):
        def run(operation):
            connections.close_all()
            try:
                with tenant_context(self.a):
                    try:
                        return operation().pk
                    except ValidationError:
                        return None
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, operations))

    def test_http_invalid_and_stale_issue_leave_quantities_unchanged(self):
        self.login("clerk")
        with tenant_context(self.a):
            held = self.reserve(quantity=2)
        path = f"/inventory/reservations/{held.reservation_id}/"
        payload = {"quantity": 3, "reason": "Synthetic oversized issue", "kind": "issue", "expected_version": 1, "operation_key": uuid.uuid4()}
        response = self.post(path, payload)
        self.assertTrue(response.context["form"].errors)
        payload.update(quantity=1, operation_key=uuid.uuid4())
        self.assertEqual(self.post(path, payload).status_code, 302)
        self.assertEqual(self.post(path, payload).status_code, 302)
        payload.update(operation_key=uuid.uuid4())
        self.assertTrue(self.post(path, payload).context["form"].errors)
        with tenant_context(self.a):
            self.assert_balance(4, 1)
            self.assertEqual(ReservationEvent.objects.count(), 2)

    def test_choice_search_is_bounded_and_branch_scoped(self):
        with tenant_context(self.a):
            services.receive_matrix(self.owner.pk, **self.values(branch_id=self.other.pk))
            cells = [{"sphere": str(i / 4), "cylinder": str(-j / 4), "quantity": 1} for i in range(34) for j in range(3)]
            services.receive_matrix(self.owner.pk, **self.values(cells=cells, create_missing=True))
            form = ReserveForm(actor_id=self.clerk.pk)
            self.assertEqual(form.fields["balance"].queryset.count(), 100)
            self.assertEqual(set(form.fields["balance"].queryset.values_list("branch_id", flat=True)), {self.main.pk})
            found = ReserveForm(actor_id=self.clerk.pk, search=self.template.sku)
            self.assertEqual(list(found.fields["balance"].queryset.values_list("variant_id", flat=True)), [self.template.pk])
            self.assertFalse(ReserveForm(actor_id=self.reader.pk, search=self.template.sku).fields["balance"].queryset.exists())

    def test_concurrent_last_unit_and_same_key(self):
        ids = self.parallel([lambda: self.reserve(quantity=5), lambda: self.reserve(quantity=5)])
        self.assertEqual(sum(item is not None for item in ids), 1)
        with tenant_context(self.a):
            self.assert_balance(5, 5)
            held = ReservationEvent.objects.get()
            self.action(held, "cancel")
        key = uuid.uuid4()
        ids = self.parallel([lambda: self.reserve(operation_key=key), lambda: self.reserve(operation_key=key)])
        self.assertEqual(ids[0], ids[1])
        with tenant_context(self.a):
            self.assert_balance(5, 5)

    def test_concurrent_issue_release_and_replayed_issue_inverse(self):
        with tenant_context(self.a):
            held = self.reserve()
        ids = self.parallel([lambda: self.action(held, "issue", quantity=5), lambda: self.action(held, "release", quantity=5)])
        self.assertEqual(sum(item is not None for item in ids), 1)
        with tenant_context(self.a):
            reservation = StockReservation.objects.get()
            self.assertEqual(reservation.held, 0)
            if reservation.issued == 0:
                held = self.reserve()
            else:
                last = ReservationEvent.objects.get(pk=ids[0] or ids[1])
                self.action(last, "reverse_issue", issue_id=last.pk)
                held = self.reserve()
        key = uuid.uuid4()
        ids = self.parallel([lambda: self.action(held, "issue", quantity=5, operation_key=key)] * 2)
        self.assertEqual(ids[0], ids[1])
        with tenant_context(self.a):
            issued = ReservationEvent.objects.get(pk=ids[0])
        inverse_key = uuid.uuid4()
        ids = self.parallel([lambda: self.action(issued, "reverse_issue", issue_id=issued.pk, operation_key=inverse_key)] * 2)
        self.assertEqual(ids[0], ids[1])
        with tenant_context(self.a):
            self.assert_balance(5, 0)

    def test_database_constraints_and_runtime_history_and_identity_protection(self):
        role = "r08_hold_" + uuid.uuid4().hex
        with tenant_context(self.a):
            held = self.reserve()
            for changes in ({"held": -1}, {"issued": 1}, {"cancelled": True}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    StockReservation.objects.update(**changes)
            with self.assertRaises(IntegrityError), transaction.atomic():
                StockMovement.objects.create(branch=self.main, variant=self.template, delta=1, before=5, after=6, reserved_after=5, variant_snapshot={})
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                for statement in ("UPDATE inventory_reservationevent SET reason=reason WHERE false", "DELETE FROM inventory_reservationevent WHERE false", "UPDATE inventory_stockreservation SET quantity=quantity WHERE false", "UPDATE inventory_stockreservation SET branch_id=branch_id WHERE false", "DELETE FROM inventory_stockreservation WHERE false"):
                    with self.subTest(statement=statement), self.assertRaises(ProgrammingError), transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                            cursor.execute(statement)
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    issued = self.action(held, "issue", quantity=1)
                    self.action(issued, "reverse_issue", issue_id=issued.pk)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
