from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import uuid
from psycopg import sql
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, Client, override_settings
from django.test.utils import CaptureQueriesContext
from django_tenants.utils import tenant_context
from access.services import assign_role, revoke_role
from directory.db_roles import grant_tenant_runtime
from inventory import services
from inventory.models import StockBalance, StockOperation, StockMovement, StockReceipt
from inventory.operations import post_operation, reverse_operation, operations_for
from inventory.reservations import reserve_stock, change_reservation
from inventory_tests import test_matrix as fixtures


@override_settings(ALLOWED_HOSTS=["a.r08.test", "b.r08.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class OperationTests(TransactionTestCase):
    login = fixtures.MatrixStockTests.login
    get = fixtures.MatrixStockTests.get
    post = fixtures.MatrixStockTests.post
    values = fixtures.MatrixStockTests.values

    def setUp(self):
        fixtures.MatrixStockTests.setUp(self)
        with tenant_context(self.a):
            services.receive_matrix(self.owner.pk, **self.values())
            self.balance = StockBalance.objects.get()

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def transfer(self, **changes):
        values = dict(source_balance_id=self.balance.pk, destination_id=self.other.pk, kind="transfer", quantity=2,
            expected_version=self.balance.version, operation_key=uuid.uuid4(), reason="Synthetic transfer")
        values.update(changes)
        return post_operation(self.owner.pk, **values)

    def count(self, **changes):
        return self.transfer(kind="count", destination_id=None, **changes)

    def inverse(self, document, **changes):
        values = dict(operation_id=document.pk, operation_key=uuid.uuid4(), reason="Synthetic inverse")
        values.update(changes)
        return reverse_operation(self.owner.pk, **values)

    def hold(self, branch=None, quantity=1):
        return reserve_stock(self.owner.pk, branch_id=branch or self.main.pk, variant_id=self.template.pk, quantity=quantity,
            operation_key=uuid.uuid4(), reason="Synthetic hold")

    def assert_balances(self, main, other=None):
        self.assertEqual(StockBalance.objects.get(branch=self.main).on_hand, main)
        if other is not None:
            self.assertEqual(StockBalance.objects.get(branch=self.other).on_hand, other)

    def test_transfer_has_equal_opposite_movements_and_a_single_inverse(self):
        with tenant_context(self.a):
            doc = self.transfer()
            self.assert_balances(3, 2)
            self.assertEqual(sum(doc.movements.values_list("delta", flat=True)), 0)
            self.assertEqual(set(doc.movements.values_list("branch_id", flat=True)), {self.main.pk, self.other.pk})
            inverse = self.inverse(doc)
            self.assert_balances(5, 0)
            self.assertEqual(inverse.reverses_id, doc.pk)
            self.assertEqual(StockOperation.objects.count(), 2)
            with self.assertRaises(ValidationError):
                self.inverse(doc)
            with self.assertRaises(ValidationError):
                self.inverse(inverse)

    def test_transfer_does_not_consume_reservations_and_inverse_protects_destination(self):
        with tenant_context(self.a):
            self.hold(quantity=4)
            self.balance.refresh_from_db()
            with self.assertRaises(ValidationError):
                self.transfer()
            doc = self.transfer(quantity=1)
            held = self.hold(self.other.pk)
            with self.assertRaises(ValidationError):
                self.inverse(doc)
            change_reservation(self.owner.pk, reservation_id=held.reservation_id, kind="issue", quantity=1, expected_version=1,
                operation_key=uuid.uuid4(), reason="Synthetic issue")
            with self.assertRaises(ValidationError):
                self.inverse(doc)
            self.assert_balances(4, 0)

    def test_replays_changed_payloads_and_stale_transfer_are_atomic(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            doc = self.transfer(operation_key=key)
            self.assertEqual(doc.pk, self.transfer(operation_key=key).pk)
            with self.assertRaises(ValidationError):
                self.transfer(operation_key=key, quantity=3)
            with self.assertRaises(ValidationError):
                self.transfer()
            inverse_key = uuid.uuid4()
            inverse = self.inverse(doc, operation_key=inverse_key)
            self.assertEqual(inverse.pk, self.inverse(doc, operation_key=inverse_key).pk)
            self.assert_balances(5, 0)

    def test_counts_increase_decrease_zero_and_unchanged_readings(self):
        with tenant_context(self.a):
            for observed in (7, 2, 0, 0):
                self.balance.refresh_from_db()
                before = self.balance.on_hand
                doc = self.count(quantity=observed)
                self.assert_balances(observed)
                self.assertEqual(doc.movements.count(), int(before != observed))
                self.assertEqual(doc.before_values[str(self.main.pk)]["on_hand"], before)
                self.assertEqual(doc.after_values[str(self.main.pk)]["on_hand"], observed)
                self.assertGreater(doc.after_values[str(self.main.pk)]["version"], doc.before_values[str(self.main.pk)]["version"])

    def test_count_rejects_below_reserved_and_old_snapshot_and_inverse_after_changes(self):
        with tenant_context(self.a):
            self.hold(quantity=3)
            self.balance.refresh_from_db()
            with self.assertRaises(ValidationError):
                self.count(quantity=2)
            key = uuid.uuid4()
            doc = self.count(quantity=4, operation_key=key)
            self.assertEqual(doc.pk, self.count(quantity=4, operation_key=key).pk)
            with self.assertRaises(ValidationError):
                self.count(quantity=4)
            services.receive_matrix(self.owner.pk, **self.values())
            with self.assertRaises(ValidationError):
                self.inverse(doc)
            self.assert_balances(9)

    def test_count_inverse_restores_quantity_without_deleting_reading(self):
        with tenant_context(self.a):
            doc = self.count(quantity=2)
            inverse = self.inverse(doc)
            self.assert_balances(5)
            self.assertEqual(list(inverse.movements.values_list("delta", flat=True)), [3])
            self.assertEqual(doc.quantity, 2)

    def test_invalid_inputs_and_inactive_catalog_do_not_create_destination(self):
        with tenant_context(self.a):
            for changes in ({"quantity": 0}, {"quantity": -1}, {"quantity": 1.5}, {"quantity": True}, {"quantity": 1000001},
                            {"destination_id": self.main.pk}, {"destination_id": None}, {"destination_id": "invalid"}, {"expected_version": 0}, {"reason": ""}):
                with self.subTest(changes=changes), self.assertRaises(ValidationError):
                    self.transfer(**changes)
            type(self.template).objects.filter(pk=self.template.pk).update(active=False)
            with self.assertRaises(ValidationError):
                self.transfer()
            self.assertEqual(StockBalance.objects.count(), 1)
            self.assertFalse(StockOperation.objects.exists())

    def test_permissions_cover_both_branches_count_is_manager_and_replay_rechecks(self):
        with tenant_context(self.a):
            values = dict(source_balance_id=self.balance.pk, destination_id=self.other.pk, kind="transfer", quantity=1, expected_version=1,
                operation_key=uuid.uuid4(), reason="Synthetic clerk transfer")
            with self.assertRaises(PermissionDenied):
                post_operation(self.clerk.pk, **values)
            grant = assign_role(self.owner.pk, user_id=self.clerk.pk, role_code="inventory_clerk", branch_id=self.other.pk)
            doc = post_operation(self.clerk.pk, **values)
            with self.assertRaises(PermissionDenied):
                post_operation(self.clerk.pk, **{**values, "kind": "count", "destination_id": None})
            with self.assertRaises(PermissionDenied):
                reverse_operation(self.clerk.pk, operation_id=doc.pk, operation_key=uuid.uuid4(), reason="Unauthorized inverse")
            revoke_role(self.owner.pk, assignment_id=grant.pk)
            with self.assertRaises(PermissionDenied):
                post_operation(self.clerk.pk, **values)

    def test_failed_movement_or_audit_rolls_back_both_balances_and_document(self):
        with tenant_context(self.a):
            for target in ("inventory.operations.StockMovement.objects.bulk_create", "inventory.operations.audit"):
                with patch(target, side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                    self.transfer()
                self.assert_balances(5)
                self.assertEqual(StockBalance.objects.count(), 1)
                self.assertFalse(StockOperation.objects.exists())

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

    def test_concurrent_transfer_same_key_and_inverse_do_not_duplicate(self):
        key = uuid.uuid4()
        ids = self.parallel([lambda: self.transfer(operation_key=key)] * 2)
        self.assertEqual(ids[0], ids[1])
        with tenant_context(self.a):
            doc = StockOperation.objects.get(pk=ids[0])
            self.assert_balances(3, 2)
        key = uuid.uuid4()
        ids = self.parallel([lambda: self.inverse(doc, operation_key=key)] * 2)
        self.assertEqual(ids[0], ids[1])
        with tenant_context(self.a):
            self.assert_balances(5, 0)

    def test_concurrent_count_and_transfer_only_one_snapshot_commits(self):
        ids = self.parallel([lambda: self.transfer(quantity=5), lambda: self.count(quantity=1)])
        self.assertEqual(sum(item is not None for item in ids), 1)
        with tenant_context(self.a):
            self.assertEqual(StockOperation.objects.count(), 1)
            self.assertGreaterEqual(StockBalance.objects.get(branch=self.main).available, 0)

    def test_http_scope_before_lists_and_lookups_and_forged_destination(self):
        with tenant_context(self.a):
            doc = self.transfer()
        path = f"/inventory/operations/{doc.pk}/"
        self.login("clerk")
        response = self.get("/inventory/operations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["documents"]), 0)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(self.get(path).status_code, 404)
        create = f"/inventory/operations/new/{self.balance.pk}/transfer/"
        response = self.post(create, {"quantity": 1, "expected_version": 2, "destination_id": self.other.pk, "operation_key": uuid.uuid4(), "reason": "Forged destination"})
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(self.get(f"/inventory/operations/new/{self.balance.pk}/count/").status_code, 403)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r08.test")
        self.assertEqual(foreign.get(path, HTTP_HOST="b.r08.test").status_code, 404)
        self.login()
        self.assertEqual(self.get(path).status_code, 200)
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(create, {}, HTTP_HOST="a.r08.test").status_code, 403)

    def test_migration_backfills_receipt_and_issue_branches_without_changing_history(self):
        with tenant_context(self.a):
            held = self.hold()
            change_reservation(self.owner.pk, reservation_id=held.reservation_id, kind="issue", quantity=1, expected_version=1,
                operation_key=uuid.uuid4(), reason="Synthetic issue before migration")
            before = list(StockMovement.objects.order_by("id").values("id", "delta", "before", "after", "variant_snapshot"))
            MigrationExecutor(connection).migrate([("inventory", "0002_stockreservation_alter_stockmovement_receipt_and_more")])
            MigrationExecutor(connection).migrate([("inventory", "0003_stockoperation_and_more")])
            self.assertEqual(list(StockMovement.objects.order_by("id").values("id", "delta", "before", "after", "variant_snapshot")), before)
            self.assertEqual(set(StockMovement.objects.values_list("branch_id", flat=True)), {self.main.pk})

    def test_database_constraints_and_runtime_immutability_allow_real_transfer_and_count(self):
        role = "r08_op_" + uuid.uuid4().hex
        with tenant_context(self.a):
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                for statement in ("UPDATE inventory_stockoperation SET reason=reason WHERE false", "DELETE FROM inventory_stockoperation WHERE false", "UPDATE inventory_stockmovement SET branch_id=branch_id WHERE false"):
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    doc = self.transfer()
                    self.inverse(doc)
                    self.balance.refresh_from_db()
                    self.count(quantity=4)
                for changes in ({"quantity": -1}, {"destination_id": self.main.pk}, {"kind": "invalid"}):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        StockOperation.objects.filter(pk=doc.pk).update(**changes)
                with self.assertRaises(IntegrityError), transaction.atomic():
                    empty_receipt = StockReceipt.objects.create(branch=self.main, kind="receipt", operation_key=uuid.uuid4(), payload_digest="a" * 64,
                        reason="Synthetic constraint probe", created_by=self.owner)
                    empty_operation = StockOperation.objects.create(source=self.main, variant=self.template, quantity=0, kind="count",
                        operation_key=uuid.uuid4(), payload_digest="b" * 64, reason="Synthetic constraint probe", created_by=self.owner,
                        before_values={}, after_values={}, variant_snapshot={})
                    StockMovement.objects.create(receipt=empty_receipt, operation=empty_operation, branch=self.main,
                        variant=self.template, delta=1, before=5, after=6, reserved_after=0, variant_snapshot={})
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_operation_list_is_paginated_and_permissions_do_not_query_per_row(self):
        with tenant_context(self.a):
            services.receive_matrix(self.owner.pk, **self.values(cells=[{"sphere": str(i / 4), "cylinder": "0", "quantity": 1} for i in range(21)], create_missing=True))
        with CaptureQueriesContext(connection) as queries:
            response = self.get("/inventory/operations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 21)
        self.assertEqual(len(response.context["page_obj"]), 20)
        self.assertLess(len(queries), 100)
