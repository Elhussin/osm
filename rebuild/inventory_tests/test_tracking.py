from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
import uuid
from psycopg import sql
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.db.models import Sum
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, Client, override_settings
from django.utils import timezone
from django_tenants.utils import tenant_context
from access.models import RoleAssignment
from access.services import revoke_role
from catalog.services import create_product, create_variant
from directory.db_roles import grant_tenant_runtime
from inventory.models import StockBalance, StockLot, StockPosition, StockReceipt, StockMovement, StockReservation, ReservationEvent, StockOperation
from inventory.receiving import receive_stock
from inventory.reservations import reserve_stock, change_reservation
from inventory.operations import post_operation, reverse_operation
from inventory.services import reverse_receipt
from inventory_tests import test_matrix as fixtures


@override_settings(ALLOWED_HOSTS=["a.r08.test", "b.r08.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class TrackingTests(TransactionTestCase):
    login = fixtures.MatrixStockTests.login
    get = fixtures.MatrixStockTests.get
    post = fixtures.MatrixStockTests.post

    def setUp(self):
        fixtures.MatrixStockTests.setUp(self)
        self.today = timezone.localdate()
        self.expiry = self.today + timedelta(days=30)
        self.variants = {"stock_lens": self.template}
        cases = [("frame", "piece", {"color": "black", "eye_size": 52, "bridge": 18, "temple": 140}),
            ("accessory", "piece", {}), ("device", "piece", {"specification": "V1"}),
            ("contact_lens", "box", {"material": "Hydrogel", "diameter": "14", "base_curve": "8.6", "sphere": "0", "pack_size": 30, "replacement": "monthly"}),
            ("service", "service", {"description": "Delivery"}),
            ("rx_lens", "piece", {k: v for k, v in fixtures.SPECS.items() if k not in {"sphere", "cylinder"}})]
        with tenant_context(self.a):
            for kind, unit, specs in cases:
                product = create_product(self.owner.pk, code_value=kind.upper(), name="Synthetic " + kind, kind=kind)
                self.variants[kind] = create_variant(self.owner.pk, product_id=product.pk, sku="TRACK-" + kind.upper(), unit=unit, base_price="20", specifications=specs)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def receipt(self, kind="contact_lens", **changes):
        values = dict(branch_id=self.main.pk, variant_id=self.variants[kind].pk, quantity=1 if kind == "device" else 5,
            operation_key=uuid.uuid4(), reason="Synthetic receive")
        if kind == "contact_lens":
            values.update(lot_code="LOT-A", expires_on=self.expiry)
        if kind == "device":
            values.update(serial="SN-1")
        values.update(changes)
        return receive_stock(self.owner.pk, **values)

    def position(self, document):
        return document.movements.select_related("position__lot").get().position

    def hold(self, position=None, *, kind="contact_lens", **changes):
        values = dict(branch_id=position.branch_id if position else self.main.pk, variant_id=position.variant_id if position else self.variants[kind].pk,
            quantity=1, operation_key=uuid.uuid4(), reason="Synthetic hold", position_id=position.pk if position else None)
        values.update(changes)
        return reserve_stock(self.owner.pk, **values)

    def change(self, event, kind, **changes):
        reservation = StockReservation.objects.get(pk=event.reservation_id)
        values = dict(reservation_id=reservation.pk, kind=kind, expected_version=reservation.version, operation_key=uuid.uuid4(), reason="Synthetic action")
        values.update(changes)
        return change_reservation(self.owner.pk, **values)

    def operation(self, position=None, *, kind="transfer", variant_kind="contact_lens", **changes):
        branch = position.branch_id if position else self.main.pk
        variant = position.variant_id if position else self.variants[variant_kind].pk
        balance = StockBalance.objects.get(branch_id=branch, variant_id=variant)
        values = dict(source_balance_id=balance.pk, kind=kind, quantity=1, expected_version=balance.version,
            operation_key=uuid.uuid4(), reason="Synthetic operation", destination_id=self.other.pk if kind == "transfer" else None)
        if position:
            position.refresh_from_db()
            values.update(position_id=position.pk, expected_position_version=position.version)
        values.update(changes)
        return post_operation(self.owner.pk, **values)

    def totals(self):
        for balance in StockBalance.objects.all():
            movements = StockMovement.objects.filter(variant_id=balance.variant_id, branch_id=balance.branch_id).aggregate(total=Sum("delta"))["total"] or 0
            reservations = StockReservation.objects.filter(variant_id=balance.variant_id, branch_id=balance.branch_id).aggregate(total=Sum("held"))["total"] or 0
            self.assertEqual((balance.on_hand, balance.reserved), (movements, reservations))
        for balance in StockBalance.objects.filter(variant__product__kind__in=["contact_lens", "device"]):
            totals = StockPosition.objects.filter(variant_id=balance.variant_id, branch_id=balance.branch_id).aggregate(hand=Sum("on_hand"), held=Sum("reserved"))
            self.assertEqual((balance.on_hand, balance.reserved), (totals["hand"] or 0, totals["held"] or 0))

    def test_plain_frame_and_accessory_full_stock_lifecycle(self):
        with tenant_context(self.a):
            for kind in ("frame", "accessory"):
                doc = self.receipt(kind)
                held = self.hold(kind=kind, quantity=2)
                issued = self.change(held, "issue", quantity=1)
                self.change(issued, "release", quantity=1)
                transfer = self.operation(kind="transfer", variant_kind=kind)
                reverse_operation(self.owner.pk, operation_id=transfer.pk, operation_key=uuid.uuid4(), reason="Synthetic transfer inverse")
                count = self.operation(kind="count", variant_kind=kind, quantity=3)
                reverse_operation(self.owner.pk, operation_id=count.pk, operation_key=uuid.uuid4(), reason="Synthetic count inverse")
                self.change(issued, "reverse_issue", issue_id=issued.pk)
                reverse_receipt(self.owner.pk, receipt_id=doc.pk, operation_key=uuid.uuid4(), reason="Synthetic receive inverse")
                self.assertEqual(StockBalance.objects.get(branch=self.main, variant=self.variants[kind]).on_hand, 0)
            self.assertFalse(StockPosition.objects.exists())

    def test_lot_allocations_partial_issue_release_and_inverse_preserve_other_lots(self):
        with tenant_context(self.a):
            first = self.position(self.receipt())
            other = self.position(self.receipt(lot_code="LOT-B", quantity=7))
            held = self.hold(first, quantity=3)
            issued = self.change(held, "issue", quantity=2)
            self.change(issued, "release", quantity=1)
            first.refresh_from_db(); other.refresh_from_db()
            self.assertEqual((first.on_hand, first.reserved, other.on_hand), (3, 0, 7))
            self.assertEqual(issued.movement.variant_snapshot["tracking"]["lot"], "LOT-A")
            self.change(issued, "reverse_issue", issue_id=issued.pk)
            first.refresh_from_db()
            self.assertEqual(first.on_hand, 5)
            self.totals()

    def test_expiry_blocks_receipt_reserve_and_later_issue_but_allows_release(self):
        with tenant_context(self.a):
            with self.assertRaises(ValidationError):
                self.receipt(expires_on=self.today - timedelta(days=1))
            doc = self.receipt(expires_on=self.today)
            position = self.position(doc)
            held = self.hold(position)
            with patch("inventory.tracking.timezone.localdate", return_value=self.today + timedelta(days=1)):
                with self.assertRaises(ValidationError):
                    self.hold(position)
                with self.assertRaises(ValidationError):
                    self.change(held, "issue", quantity=1)
                self.change(held, "cancel")
                self.operation(position, quantity=2)
            self.totals()

    def test_lot_expiry_is_immutable_and_plain_types_reject_tracking_fields(self):
        with tenant_context(self.a):
            self.receipt()
            with self.assertRaises(ValidationError):
                self.receipt(expires_on=self.expiry + timedelta(days=1))
            self.assertEqual(StockLot.objects.get().expires_on, self.expiry)
            for kind in ("frame", "accessory", "stock_lens"):
                with self.assertRaises(ValidationError):
                    self.receipt(kind, serial="INVALID")
            for kind in ("service", "rx_lens"):
                with self.assertRaises(ValidationError):
                    self.receipt(kind)
            self.totals()

    def test_serial_is_unique_for_all_items_and_retained_after_issue(self):
        with tenant_context(self.a):
            position = self.position(self.receipt("device"))
            other = create_variant(self.owner.pk, product_id=self.variants["device"].product_id, sku="SECOND-DEVICE", unit="piece", base_price="20", specifications={"specification": "V2"})
            for changes in ({"variant_id": other.pk}, {"quantity": 2, "serial": "SN-2"}):
                with self.assertRaises(ValidationError):
                    self.receipt("device", **changes)
            held = self.hold(position)
            issued = self.change(held, "issue", quantity=1)
            with self.assertRaises(ValidationError):
                self.receipt("device")
            self.change(issued, "reverse_issue", issue_id=issued.pk)
            position.refresh_from_db()
            self.assertEqual(position.on_hand, 1)
            self.totals()

    def test_serial_transfer_preserves_one_identity_and_inverse_cannot_use_another_unit(self):
        with tenant_context(self.a):
            original_receipt = self.receipt("device")
            position = self.position(original_receipt)
            self.receipt("device", branch_id=self.other.pk, serial="SN-2")
            self.receipt("device", serial="SN-3")
            first = self.operation(position)
            position.refresh_from_db()
            self.assertEqual(position.branch_id, self.other.pk)
            self.assertEqual(set(first.movements.values_list("position_id", flat=True)), {position.pk})
            with self.assertRaises(ValidationError):
                reverse_receipt(self.owner.pk, receipt_id=original_receipt.pk, operation_key=uuid.uuid4(), reason="Cannot use SN-3")
            held = self.hold(position)
            with self.assertRaises(ValidationError):
                reverse_operation(self.owner.pk, operation_id=first.pk, operation_key=uuid.uuid4(), reason="Blocked held unit")
            self.change(held, "cancel")
            second = self.operation(position, destination_id=self.main.pk)
            with self.assertRaises(ValidationError):
                reverse_operation(self.owner.pk, operation_id=first.pk, operation_key=uuid.uuid4(), reason="Wrong unit location")
            reverse_operation(self.owner.pk, operation_id=second.pk, operation_key=uuid.uuid4(), reason="Undo second")
            reverse_operation(self.owner.pk, operation_id=first.pk, operation_key=uuid.uuid4(), reason="Undo first")
            position.refresh_from_db()
            self.assertEqual(position.branch_id, self.main.pk)
            self.assertEqual(StockPosition.objects.filter(serial__isnull=False).count(), 3)
            self.totals()

    def test_lot_transfer_count_and_inverse_update_identity_and_aggregate(self):
        with tenant_context(self.a):
            position = self.position(self.receipt())
            doc = self.operation(position, quantity=3)
            destination = StockPosition.objects.get(lot=position.lot, branch=self.other)
            self.assertEqual(destination.on_hand, 3)
            held = self.hold(destination)
            with self.assertRaises(ValidationError):
                reverse_operation(self.owner.pk, operation_id=doc.pk, operation_key=uuid.uuid4(), reason="Blocked held lot")
            self.change(held, "cancel")
            reverse_operation(self.owner.pk, operation_id=doc.pk, operation_key=uuid.uuid4(), reason="Undo transfer")
            count = self.operation(position, kind="count", quantity=2)
            self.assertEqual(StockBalance.objects.get(branch=self.main, variant=position.variant).on_hand, 2)
            reverse_operation(self.owner.pk, operation_id=count.pk, operation_key=uuid.uuid4(), reason="Undo count")
            position.refresh_from_db()
            self.assertEqual(position.on_hand, 5)
            self.totals()

    def test_serial_count_zero_one_and_later_count_invalidate_old_inverse(self):
        with tenant_context(self.a):
            position = self.position(self.receipt("device"))
            with self.assertRaises(ValidationError):
                self.operation(position, kind="count", quantity=2)
            missing = self.operation(position, kind="count", quantity=0)
            reverse_operation(self.owner.pk, operation_id=missing.pk, operation_key=uuid.uuid4(), reason="Restore counted unit")
            same = self.operation(position, kind="count", quantity=1)
            self.assertEqual(same.movements.count(), 0)
            self.operation(position, kind="count", quantity=1)
            with self.assertRaises(ValidationError):
                reverse_operation(self.owner.pk, operation_id=same.pk, operation_key=uuid.uuid4(), reason="Stale count")
            self.totals()

    def test_missing_wrong_position_and_receipt_inverse_cannot_consume_other_lot(self):
        with tenant_context(self.a):
            first = self.receipt(quantity=1)
            position = self.position(first)
            self.receipt(lot_code="LOT-B", quantity=9)
            with self.assertRaises(ValidationError):
                self.hold()
            with self.assertRaises(ValidationError):
                self.operation(kind="count", quantity=1)
            with self.assertRaises(ValidationError):
                self.hold(position, branch_id=self.other.pk)
            device = self.position(self.receipt("device"))
            with self.assertRaises(ValidationError):
                reserve_stock(self.owner.pk, branch_id=self.main.pk, variant_id=position.variant_id, position_id=device.pk,
                    quantity=1, operation_key=uuid.uuid4(), reason="Wrong identity type")
            held = self.hold(position)
            self.change(held, "issue", quantity=1)
            with self.assertRaises(ValidationError):
                reverse_receipt(self.owner.pk, receipt_id=first.pk, operation_key=uuid.uuid4(), reason="Cannot use LOT-B")
            self.totals()

    def test_idempotence_changed_payload_and_revocation(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            first = self.receipt(operation_key=key)
            self.assertEqual(first.pk, self.receipt(operation_key=key).pk)
            with self.assertRaises(ValidationError):
                self.receipt(operation_key=key, quantity=4)
            position = self.position(first)
            key = uuid.uuid4()
            held = self.hold(position, operation_key=key)
            self.assertEqual(held.pk, self.hold(position, operation_key=key).pk)
            clerk_values = dict(branch_id=self.main.pk, variant_id=position.variant_id, quantity=1, lot_code="LOT-CLERK",
                expires_on=self.expiry, operation_key=uuid.uuid4(), reason="Clerk receipt")
            clerk_receipt = receive_stock(self.clerk.pk, **clerk_values)
            clerk_position = self.position(clerk_receipt)
            clerk_hold = dict(branch_id=self.main.pk, variant_id=position.variant_id, position_id=clerk_position.pk,
                quantity=1, operation_key=uuid.uuid4(), reason="Clerk hold")
            reserve_stock(self.clerk.pk, **clerk_hold)
            with self.assertRaises(PermissionDenied):
                receive_stock(self.clerk.pk, branch_id=self.other.pk, variant_id=position.variant_id, quantity=1, lot_code="OTHER", expires_on=self.expiry, operation_key=uuid.uuid4(), reason="Denied branch")
            revoke_role(self.owner.pk, assignment_id=self.clerk_grant.pk)
            with self.assertRaises(PermissionDenied):
                receive_stock(self.clerk.pk, **clerk_values)
            with self.assertRaises(PermissionDenied):
                reserve_stock(self.clerk.pk, **clerk_hold)
            self.totals()

    def test_rollback_of_receipt_transfer_and_issue_includes_tracking_rows(self):
        with tenant_context(self.a):
            with patch("inventory.receiving.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.receipt()
            self.assertFalse(StockLot.objects.exists())
            self.assertFalse(StockPosition.objects.exists())
            self.assertFalse(StockBalance.objects.exists())
            position = self.position(self.receipt())
            with patch("inventory.operations.StockMovement.objects.bulk_create", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.operation(position)
            self.assertEqual(StockPosition.objects.count(), 1)
            held = self.hold(position)
            with patch("inventory.reservations.StockMovement.objects.create", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.change(held, "issue", quantity=1)
            position.refresh_from_db()
            self.assertEqual((position.on_hand, position.reserved), (5, 1))
            self.totals()

    def parallel(self, actions):
        def run(action):
            connections.close_all()
            try:
                with tenant_context(self.a):
                    try:
                        return action().pk
                    except ValidationError:
                        return None
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, actions))

    def test_concurrent_last_lot_unit_and_duplicate_serial(self):
        with tenant_context(self.a):
            position = self.position(self.receipt(quantity=1))
        results = self.parallel([lambda: self.hold(position)] * 2)
        self.assertEqual(sum(value is not None for value in results), 1)
        results = self.parallel([lambda: self.receipt("device")] * 2)
        self.assertEqual(sum(value is not None for value in results), 1)
        key = uuid.uuid4()
        results = self.parallel([lambda: self.receipt("device", serial="SN-2", operation_key=key)] * 2)
        self.assertEqual(results[0], results[1])
        with tenant_context(self.a):
            self.totals()

    def test_http_scope_trace_and_expiry_view_and_csrf(self):
        with tenant_context(self.a):
            position = self.position(self.receipt("device", branch_id=self.other.pk))
        self.login("clerk")
        response = self.get("/inventory/positions/")
        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertEqual(self.get(f"/inventory/positions/{position.pk}/reserve/").status_code, 404)
        self.assertEqual(self.get("/inventory/trace/?q=SN-1").context["page_obj"].paginator.count, 0)
        self.login()
        self.assertEqual(self.get("/inventory/trace/?q=SN-1").context["page_obj"].paginator.count, 1)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r08.test")
        self.assertEqual(foreign.get(f"/inventory/positions/{position.pk}/reserve/", HTTP_HOST="b.r08.test").status_code, 404)
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(f"/inventory/receiving/{self.variants['device'].pk}/", {}, HTTP_HOST="a.r08.test").status_code, 403)

    def test_migration_rejects_unmapped_tracked_history_and_preserves_plain_history(self):
        with tenant_context(self.a):
            self.receipt("frame")
            before = list(StockMovement.objects.values("id", "delta", "variant_snapshot"))
            MigrationExecutor(connection).migrate([("inventory", "0003_stockoperation_and_more")])
            with transaction.atomic():
                StockBalance.objects.create(variant=self.variants["device"], branch=self.main, on_hand=1)
                with self.assertRaises(RuntimeError):
                    MigrationExecutor(connection).migrate([("inventory", "0004_stocklot_stockposition_stockmovement_position_and_more")])
                transaction.set_rollback(True)
            MigrationExecutor(connection).migrate([("inventory", "0004_stocklot_stockposition_stockmovement_position_and_more")])
            self.assertEqual(list(StockMovement.objects.values("id", "delta", "variant_snapshot")), before)

    def test_database_constraints_and_runtime_identity_protection_with_real_workflows(self):
        role = "r08_track_" + uuid.uuid4().hex
        with tenant_context(self.a):
            position = self.position(self.receipt("device"))
            lot_position = self.position(self.receipt(lot_code="PROBE"))
            for changes in ({"on_hand": 2}, {"reserved": 2}, {"lot": None, "serial": None}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    StockPosition.objects.filter(pk=position.pk).update(**changes)
            with self.assertRaises(IntegrityError), transaction.atomic():
                StockPosition.objects.create(variant=position.variant, branch=self.other, serial="SN-1", created_by=self.owner)
            with self.assertRaises(IntegrityError), transaction.atomic():
                StockLot.objects.create(variant=lot_position.variant, code="PROBE", expires_on=self.expiry + timedelta(days=1), created_by=self.owner)
            with self.assertRaises(IntegrityError), transaction.atomic():
                StockPosition.objects.create(variant=lot_position.variant, branch=self.main, lot=lot_position.lot, created_by=self.owner)
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                for statement in ("UPDATE inventory_stocklot SET expires_on=expires_on WHERE false", "DELETE FROM inventory_stocklot WHERE false", "UPDATE inventory_stockposition SET serial=serial WHERE false", "UPDATE inventory_stockposition SET variant_id=variant_id WHERE false", "DELETE FROM inventory_stockposition WHERE false"):
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    lot = self.position(self.receipt())
                    held = self.hold(lot)
                    issued = self.change(held, "issue", quantity=1)
                    self.change(issued, "reverse_issue", issue_id=issued.pk)
                    transfer = self.operation(lot)
                    reverse_operation(self.owner.pk, operation_id=transfer.pk, operation_key=uuid.uuid4(), reason="Runtime lot inverse")
                    self.operation(lot, kind="count", quantity=4)
                    transfer = self.operation(position)
                    reverse_operation(self.owner.pk, operation_id=transfer.pk, operation_key=uuid.uuid4(), reason="Runtime serial inverse")
                self.totals()
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
