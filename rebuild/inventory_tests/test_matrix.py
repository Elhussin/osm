from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import importlib
from unittest.mock import patch
import uuid
import time
from psycopg import sql
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.test import Client, SimpleTestCase, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django_tenants.utils import tenant_context, schema_context
from access.models import Branch, AuditEvent
from access.services import create_branch, create_member, assign_role, revoke_role
from catalog.models import Variant
from catalog.services import create_product, create_variant, update_variant
from catalog.specifications import stock_matrix_fields
from directory.provisioning import provision_company
from directory.db_roles import grant_tenant_runtime
from inventory import services
from inventory.matrix import axes, normalize_cells
from inventory.models import StockBalance, StockReceipt, StockMovement
from inventory.views import SALT

PASSWORD = "Synthetic-Matrix-2026!"
SPECS = {"material": "Resin", "index": "1.60", "diameter": "70", "design": "single", "coatings": "AR, UV", "sphere": "0", "cylinder": "0"}


class MatrixShapeTests(SimpleTestCase):
    def test_axes_and_cells_are_bounded_and_zero_is_not_an_addition(self):
        rows, columns = axes("-0.25", "0.25", "-0.25", "0")
        self.assertEqual(rows, [Decimal("0.25"), Decimal("0"), Decimal("-0.25")])
        self.assertEqual(columns, [Decimal("0"), Decimal("-0.25")])
        self.assertEqual(normalize_cells([{"sphere": "-0.00", "cylinder": "0", "quantity": 2}, {"sphere": "0.25", "cylinder": "0", "quantity": 0}]), [{"sphere": "0.00", "cylinder": "0.00", "quantity": 2}])
        for values in (("-40", "40", "-20", "20"), ("1", "-1", "0", "0"), ("0.1", "1", "0", "0")):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                axes(*values)

    def test_fractional_negative_duplicate_and_empty_quantities_rejected(self):
        for value in (-1, "1.5", "NaN", True, 1.0, 1000001):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                normalize_cells([{"sphere": "0", "cylinder": "0", "quantity": value}])
        for cells in ([], [{"sphere": "0", "cylinder": "0", "quantity": 0}], [{"sphere": "0", "cylinder": "0", "quantity": 1}] * 2):
            with self.assertRaises(ValidationError):
                normalize_cells(cells)


@override_settings(ALLOWED_HOSTS=["a.r08.test", "b.r08.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MatrixStockTests(TransactionTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        self.a = provision_company(name="Synthetic Matrix A", domain="a.r08.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        self.b = provision_company(name="Synthetic Matrix B", domain="b.r08.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        with tenant_context(self.a):
            self.owner = get_user_model().objects.get(username="owner")
            self.main = Branch.objects.get(code="MAIN")
            self.other = create_branch(self.owner.pk, code="SECOND", name="Other branch")
            self.clerk = create_member(self.owner.pk, username="clerk", password=PASSWORD)
            self.clerk_grant = assign_role(self.owner.pk, user_id=self.clerk.pk, role_code="inventory_clerk", branch_id=self.main.pk)
            assign_role(self.owner.pk, user_id=self.clerk.pk, role_code="catalog_reader")
            self.reader = create_member(self.owner.pk, username="reader", password=PASSWORD)
            assign_role(self.owner.pk, user_id=self.reader.pk, role_code="catalog_reader")
            self.product = create_product(self.owner.pk, code_value="LENS", name="Synthetic lens", kind="stock_lens")
            self.template = create_variant(self.owner.pk, product_id=self.product.pk, sku="LENS-0", unit="piece", base_price="20.00", specifications=SPECS)
        self.login()

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def login(self, username="owner"):
        self.client = Client()
        self.assertEqual(self.client.post("/auth/login/", {"username": username, "password": PASSWORD}, HTTP_HOST="a.r08.test").status_code, 302)

    def get(self, path):
        return self.client.get(path, HTTP_HOST="a.r08.test")

    def post(self, path, data):
        return self.client.post(path, data, HTTP_HOST="a.r08.test")

    def values(self, **kwargs):
        values = {"product_id": self.product.pk, "template_id": self.template.pk, "branch_id": self.main.pk,
            "operation_key": uuid.uuid4(), "template_version": 1, "reason": "Synthetic receipt", "cells": [{"sphere": "0", "cylinder": "0", "quantity": 5}]}
        values.update(kwargs)
        return values

    def entry_data(self):
        return {"branch_id": self.main.pk, "template_id": self.template.pk, "sphere_min": "0", "sphere_max": "0.25", "cylinder_min": "-0.25", "cylinder_max": "0",
            "operation_key": uuid.uuid4(), "template_version": 1, "reason": "Synthetic receipt", "create_missing": "no", "q_1_0": "5"}

    def test_preview_has_no_effect_receipt_adds_and_replay_does_not_duplicate(self):
        with tenant_context(self.a):
            values = self.values()
            preview = services.preview_receipt(self.owner.pk, **values)
            self.assertEqual(preview["total"], 5)
            self.assertEqual(StockReceipt.objects.count(), 0)
            first = services.receive_matrix(self.owner.pk, **values)
            replay = services.receive_matrix(self.owner.pk, **values)
            self.assertEqual(first.pk, replay.pk)
            self.assertEqual(StockBalance.objects.get().on_hand, 5)
            self.assertEqual(StockMovement.objects.count(), 1)
            services.receive_matrix(self.owner.pk, **self.values())
            self.assertEqual(StockBalance.objects.get().on_hand, 10)
            with self.assertRaises(ValidationError):
                services.receive_matrix(self.owner.pk, **{**values, "reason": "Changed payload"})

    def test_grouping_separates_coatings_material_and_unit(self):
        with tenant_context(self.a):
            variants = [self.template]
            for i, specs, unit in ((1, {**SPECS, "coatings": "UV"}, "piece"), (2, {**SPECS, "material": "Glass"}, "piece"), (3, SPECS, "pair")):
                variants.append(create_variant(self.owner.pk, product_id=self.product.pk, sku=f"LENS-{i}", unit=unit, base_price="20", specifications=specs))
            self.assertEqual(len({v.matrix_family for v in variants}), 4)
            same = create_variant(self.owner.pk, product_id=self.product.pk, sku="LENS-025", unit="piece", base_price="20", specifications={**SPECS, "sphere": "0.25", "coatings": "uv, ar, ar"})
            self.assertEqual(same.matrix_family, self.template.matrix_family)
        response = self.get(f"/inventory/lenses/{self.product.pk}/")
        self.assertEqual(response.status_code, 200)
        with tenant_context(self.a):
            self.assertEqual(response.context["filters"].fields["template_id"].queryset.count(), 4)

    def test_missing_cells_created_only_with_catalog_permission_and_nonzero_quantity(self):
        with tenant_context(self.a):
            cells = [{"sphere": "0.25", "cylinder": "0", "quantity": 4}, {"sphere": "0.50", "cylinder": "0", "quantity": 0}]
            with self.assertRaises(ValidationError):
                services.receive_matrix(self.clerk.pk, **self.values(cells=cells))
            with self.assertRaises(PermissionDenied):
                services.receive_matrix(self.clerk.pk, **self.values(cells=cells, create_missing=True))
            receipt = services.receive_matrix(self.owner.pk, **self.values(cells=cells, create_missing=True))
            self.assertEqual(Variant.objects.count(), 2)
            new = receipt.movements.get().variant
            self.assertEqual(new.sphere, Decimal("0.25"))
            self.assertEqual(new.base_price, Decimal("20.00"))
            self.assertEqual(new.matrix_family, self.template.matrix_family)
            self.assertEqual(StockBalance.objects.get().on_hand, 4)

    def test_failure_rolls_back_new_variants_balances_and_document(self):
        with tenant_context(self.a):
            with patch("inventory.services.StockMovement.objects.bulk_create", side_effect=RuntimeError("Synthetic failure")):
                with self.assertRaises(RuntimeError):
                    services.receive_matrix(self.owner.pk, **self.values(create_missing=True, cells=[{"sphere": "1", "cylinder": "0", "quantity": 2}]))
            self.assertEqual(Variant.objects.count(), 1)
            self.assertEqual(StockReceipt.objects.count(), 0)
            self.assertEqual(StockBalance.objects.count(), 0)

    def test_bulk_matrix_creates_twelve_cells_without_per_cell_database_roundtrips(self):
        cells = [{"sphere": str(Decimal(i) / 4), "cylinder": str(-Decimal(j) / 4), "quantity": 1} for i in range(1, 5) for j in range(3)]
        with tenant_context(self.a), CaptureQueriesContext(connection) as queries:
            document = services.receive_matrix(self.owner.pk, **self.values(cells=cells, create_missing=True))
        self.assertLess(len(queries), 100, "Bulk receipt exceeded the query budget")
        with tenant_context(self.a):
            self.assertEqual(document.movements.count(), 12)
            self.assertEqual(StockBalance.objects.count(), 12)

    def test_signed_preview_confirm_edit_and_repeat(self):
        response = self.post(f"/inventory/lenses/{self.product.pk}/", self.entry_data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مراجعة إضافة المخزون")
        token = response.context["confirm_form"].initial["preview_token"]
        with tenant_context(self.a):
            self.assertEqual(StockReceipt.objects.count(), 0)
        result = self.post("/inventory/receipts/confirm/", {"preview_token": token})
        self.assertEqual(result.status_code, 302)
        replay = self.post("/inventory/receipts/confirm/", {"preview_token": token})
        self.assertEqual(replay.url, result.url)
        with tenant_context(self.a):
            self.assertEqual(StockBalance.objects.get().on_hand, 5)

    def test_bad_or_foreign_actor_company_and_expired_preview_rejected(self):
        response = self.post(f"/inventory/lenses/{self.product.pk}/", self.entry_data())
        token = response.context["confirm_form"].initial["preview_token"]
        self.assertEqual(self.post("/inventory/receipts/confirm/", {"preview_token": token + "tampered"}).status_code, 422)
        self.login("clerk")
        self.assertEqual(self.post("/inventory/receipts/confirm/", {"preview_token": token}).status_code, 403)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="b.r08.test")
        self.assertEqual(foreign.post("/inventory/receipts/confirm/", {"preview_token": token}, HTTP_HOST="b.r08.test").status_code, 403)
        self.login()
        with patch("django.core.signing.time.time", return_value=time.time() + 901):
            self.assertEqual(self.post("/inventory/receipts/confirm/", {"preview_token": token}).status_code, 422)
        with tenant_context(self.a):
            self.assertEqual(StockReceipt.objects.count(), 0)

    def test_preview_stale_template_and_revoked_permission_fail_at_commit(self):
        with tenant_context(self.a):
            values = self.values()
            services.preview_receipt(self.owner.pk, **values)
            update_variant(self.owner.pk, variant_id=self.template.pk, expected_version=1, base_price="21", active=True)
            with self.assertRaises(ValidationError):
                services.receive_matrix(self.owner.pk, **values)
            values = self.values(template_version=2)
            services.preview_receipt(self.clerk.pk, **values)
            revoke_role(self.owner.pk, assignment_id=self.clerk_grant.pk)
            with self.assertRaises(PermissionDenied):
                services.receive_matrix(self.clerk.pk, **values)
            self.assertEqual(StockBalance.objects.count(), 0)

    def test_scope_before_balance_totals_and_receipt_lookup(self):
        with tenant_context(self.a):
            doc = services.receive_matrix(self.owner.pk, **self.values(branch_id=self.other.pk))
        self.login("clerk")
        matrix = self.get(f"/inventory/lenses/{self.product.pk}/")
        self.assertEqual(matrix.context["family_on_hand"], 0)
        self.assertEqual(self.get(f"/inventory/receipts/{doc.pk}/").status_code, 404)
        self.assertEqual(self.get(f"/inventory/lenses/{self.product.pk}/?branch_id={self.other.pk}").status_code, 422)
        with tenant_context(self.a):
            with self.assertRaises(PermissionDenied):
                services.receive_matrix(self.clerk.pk, **self.values(branch_id=self.other.pk))
        self.login("reader")
        self.assertEqual(self.get(f"/inventory/lenses/{self.product.pk}/").status_code, 403)

    def test_concurrent_receipts_do_not_lose_updates_and_same_key_only_once(self):
        shared = self.values()
        def receive(values):
            connections.close_all()
            try:
                with tenant_context(self.a):
                    return services.receive_matrix(self.owner.pk, **values).pk
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(receive, [shared, shared]))
        self.assertEqual(ids[0], ids[1])
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(receive, [self.values(), self.values()]))
        with tenant_context(self.a):
            self.assertEqual(StockBalance.objects.get().on_hand, 15)
            self.assertEqual(StockMovement.objects.count(), 3)
        reverse_key = uuid.uuid4()
        def reverse(_):
            connections.close_all()
            try:
                with tenant_context(self.a):
                    return services.reverse_receipt(self.owner.pk, receipt_id=ids[0], operation_key=reverse_key, reason="Concurrent inverse").pk
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            inverses = list(pool.map(reverse, range(2)))
        self.assertEqual(inverses[0], inverses[1])
        with tenant_context(self.a):
            self.assertEqual(StockBalance.objects.get().on_hand, 10)
            self.assertEqual(StockMovement.objects.count(), 4)

    def test_reversal_is_auditable_idempotent_and_does_not_delete_variants(self):
        with tenant_context(self.a):
            doc = services.receive_matrix(self.owner.pk, **self.values())
            key = uuid.uuid4()
            reverse = services.reverse_receipt(self.owner.pk, receipt_id=doc.pk, operation_key=key, reason="Synthetic correction")
            self.assertEqual(services.reverse_receipt(self.owner.pk, receipt_id=doc.pk, operation_key=key, reason="Synthetic correction").pk, reverse.pk)
            self.assertEqual(StockBalance.objects.get().on_hand, 0)
            self.assertEqual(StockReceipt.objects.count(), 2)
            self.assertEqual(StockMovement.objects.get(receipt=reverse).delta, -5)
            self.assertEqual(Variant.objects.count(), 1)
            with self.assertRaises(ValidationError):
                services.reverse_receipt(self.owner.pk, receipt_id=doc.pk, operation_key=uuid.uuid4(), reason="Again")

    def test_reversal_rejects_used_or_reserved_quantities_atomically(self):
        with tenant_context(self.a):
            doc = services.receive_matrix(self.owner.pk, **self.values())
            StockBalance.objects.update(reserved=1)
            with self.assertRaises(ValidationError):
                services.reverse_receipt(self.owner.pk, receipt_id=doc.pk, operation_key=uuid.uuid4(), reason="Reserved")
            StockBalance.objects.update(reserved=0, on_hand=4)
            with self.assertRaises(ValidationError):
                services.reverse_receipt(self.owner.pk, receipt_id=doc.pk, operation_key=uuid.uuid4(), reason="Used")
            self.assertEqual(StockReceipt.objects.count(), 1)
            self.assertEqual(StockBalance.objects.get().on_hand, 4)
            with self.assertRaises(PermissionDenied):
                services.reverse_receipt(self.clerk.pk, receipt_id=doc.pk, operation_key=uuid.uuid4(), reason="Unauthorized")

    def test_invalid_quantity_inactive_variant_or_extra_grid_fields_have_no_effect(self):
        data = self.entry_data()
        for changes in ({"q_1_0": "-1"}, {"q_1_0": "1.5"}, {"q_999_0": "1"}, {"q_1_0": "", "q_0_0": "2"}):
            self.assertEqual(self.post(f"/inventory/lenses/{self.product.pk}/", {**data, **changes}).status_code, 422)
        with tenant_context(self.a):
            update_variant(self.owner.pk, variant_id=self.template.pk, expected_version=1, base_price="20", active=False)
        self.assertEqual(self.post(f"/inventory/lenses/{self.product.pk}/", data).status_code, 403)
        with tenant_context(self.a):
            self.assertEqual(StockReceipt.objects.count(), 0)

    def test_backfill_preserves_existing_variants_and_prices(self):
        migration = importlib.import_module("catalog.migrations.0002_variant_cylinder_variant_matrix_family_and_more")
        with tenant_context(self.a):
            Variant.objects.filter(pk=self.template.pk).update(matrix_family=None, sphere=None, cylinder=None)
            with connection.schema_editor() as editor:
                migration.backfill_stock_matrix(apps, editor)
            self.template.refresh_from_db()
            self.assertEqual(self.template.matrix_family, stock_matrix_fields(self.template.specifications)["matrix_family"])
            self.assertEqual(self.template.sphere, Decimal("0"))
            self.assertEqual(self.template.base_price, Decimal("20.00"))
            self.assertEqual(self.template.sku, "LENS-0")

    def test_database_balance_and_movement_constraints_and_public_absence(self):
        with schema_context("public"), connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'inventory_%'")
            self.assertEqual(cursor.fetchall(), [])
        with tenant_context(self.a):
            document = services.receive_matrix(self.owner.pk, **self.values())
            for changes in ({"on_hand": -1}, {"reserved": 6}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    StockBalance.objects.update(**changes)
            with self.assertRaises(IntegrityError), transaction.atomic():
                StockMovement.objects.update(after=99)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="b.r08.test")
        for path in (f"/inventory/lenses/{self.product.pk}/", f"/inventory/receipts/{document.pk}/"):
            self.assertEqual(foreign.get(path, HTTP_HOST="b.r08.test").status_code, 404)

    def test_runtime_cannot_change_or_delete_posted_documents_or_matrix_identity(self):
        role = "r08_probe_" + uuid.uuid4().hex
        with tenant_context(self.a):
            services.receive_matrix(self.owner.pk, **self.values())
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
            try:
                statements = ["UPDATE inventory_stockreceipt SET reason=reason WHERE false", "DELETE FROM inventory_stockreceipt WHERE false", "UPDATE inventory_stockmovement SET delta=delta WHERE false", "DELETE FROM inventory_stockmovement WHERE false", "DELETE FROM inventory_stockbalance WHERE false", "UPDATE catalog_variant SET matrix_family=matrix_family WHERE false"]
                for statement in statements:
                    with self.subTest(statement=statement), self.assertRaises(ProgrammingError) as error, transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                            cursor.execute(statement)
                    self.assertEqual(getattr(error.exception.__cause__, "sqlstate", None), "42501")
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
