import base64
import uuid
from unittest.mock import patch
from xml.etree import ElementTree as ET
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TransactionTestCase, Client, override_settings
from django_tenants.utils import tenant_context
from django.db import connection
from access.models import AuditEvent, RoleAssignment
from access.services import revoke_role
from catalog.services import create_variant, create_product
from catalog.models import Variant
from inventory.labels import barcode_image, label_preview
from inventory.models import StockBalance, StockMovement, StockReceipt
from inventory.services import receive_matrix
from inventory_tests import test_matrix as fixtures


class LabelImageTests(SimpleTestCase):
    def test_svg_has_physical_dimensions_and_no_external_dtd_or_scripts(self):
        image = barcode_image("LENS-0123")
        svg = base64.b64decode(image["uri"].split(",", 1)[1])
        root = ET.fromstring(svg)
        self.assertTrue(root.attrib["width"].endswith("mm"))
        self.assertEqual(root.attrib["height"], "14.000mm")
        self.assertGreater(len(list(root.iter("{http://www.w3.org/2000/svg}rect"))), 10)
        for forbidden in (b"DOCTYPE", b"<script", b"href=", b"<text"):
            self.assertNotIn(forbidden, svg)

    def test_invalid_codes_are_rejected_without_interpolation(self):
        for value in ("", "<svg>", "lower", "A\nB", "A" * 81, None):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                barcode_image(value)


@override_settings(ALLOWED_HOSTS=["a.r08.test", "b.r08.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class LabelTests(TransactionTestCase):
    login = fixtures.MatrixStockTests.login
    get = fixtures.MatrixStockTests.get
    post = fixtures.MatrixStockTests.post
    values = fixtures.MatrixStockTests.values

    def setUp(self):
        fixtures.MatrixStockTests.setUp(self)
        self.path = f"/catalog/variants/{self.template.pk}/labels/"

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def test_sku_fallback_and_registered_barcode_preference_without_stock_effect(self):
        with tenant_context(self.a):
            receive_matrix(self.owner.pk, **self.values())
            before = list(StockBalance.objects.values("on_hand", "reserved", "version"))
            audit_count = AuditEvent.objects.count()
            data = label_preview(self.reader.pk, variant_id=self.template.pk, copies=13)
            self.assertEqual(data["code_value"], self.template.sku)
            self.assertTrue(data["specs"].startswith("SPH: 0.00 · CYL: 0.00"))
            self.assertEqual([len(sheet) for sheet in data["sheets"]], [12, 1])
            self.assertEqual(list(StockBalance.objects.values("on_hand", "reserved", "version")), before)
            self.assertEqual(StockMovement.objects.count(), 1)
            self.assertEqual(StockReceipt.objects.count(), 1)
            self.assertEqual(AuditEvent.objects.count(), audit_count)
            variant = create_variant(self.owner.pk, product_id=self.product.pk, sku="LENS-OTHER", barcode="1234567890123", unit="piece", base_price="30", specifications={**fixtures.SPECS, "sphere": "0.25"})
            self.assertEqual(label_preview(self.reader.pk, variant_id=variant.pk, copies=1)["code_value"], variant.barcode)

    def test_layout_auto_wide_and_reject_too_narrow_without_truncating(self):
        with tenant_context(self.a):
            variant = create_variant(self.owner.pk, product_id=self.product.pk, sku="W" * 60, unit="piece", base_price="30", specifications={**fixtures.SPECS, "sphere": "0.25"})
            data = label_preview(self.owner.pk, variant_id=variant.pk, copies=5)
            self.assertEqual(data["layout"], "wide")
            self.assertEqual(data["code_value"], variant.sku)
            self.assertEqual([len(sheet) for sheet in data["sheets"]], [4, 1])
            with self.assertRaises(ValidationError):
                label_preview(self.owner.pk, variant_id=variant.pk, copies=1, layout="standard")

    def test_limits_and_cross_sku_barcode_ambiguity(self):
        with tenant_context(self.a):
            self.assertEqual(len(label_preview(self.owner.pk, variant_id=self.template.pk, copies=120)["sheets"]), 10)
            for copies in (0, -1, 121, 1.0, True, "1.5"):
                with self.subTest(copies=copies), self.assertRaises(ValidationError):
                    label_preview(self.owner.pk, variant_id=self.template.pk, copies=copies)
            with self.assertRaises(ValidationError):
                label_preview(self.owner.pk, variant_id=self.template.pk, copies=1, layout="unknown")
            legacy = create_variant(self.owner.pk, product_id=self.product.pk, sku="OTHER", unit="piece", base_price="30", specifications={**fixtures.SPECS, "sphere": "0.25"})
            # Simulate a conflict inherited from before cross-column service validation.
            Variant.objects.filter(pk=legacy.pk).update(barcode=self.template.sku)
            with self.assertRaises(ValidationError):
                label_preview(self.owner.pk, variant_id=self.template.pk, copies=1)

    def test_new_catalog_and_matrix_identifiers_cannot_ambiguate_existing_labels(self):
        with tenant_context(self.a):
            with self.assertRaises(ValidationError):
                create_variant(self.owner.pk, product_id=self.product.pk, sku="OTHER", barcode=self.template.sku, unit="piece", base_price="30", specifications={**fixtures.SPECS, "sphere": "0.25"})
            fixed = uuid.UUID("01234567-89ab-cdef-0123-456789abcdef")
            reserved_code = "MX-" + fixed.hex.upper()
            create_variant(self.owner.pk, product_id=self.product.pk, sku="OTHER", barcode=reserved_code, unit="piece", base_price="30", specifications={**fixtures.SPECS, "sphere": "0.25"})
            with self.assertRaises(ValidationError):
                create_variant(self.owner.pk, product_id=self.product.pk, sku=reserved_code, unit="piece", base_price="30", specifications={**fixtures.SPECS, "sphere": "0.5"})
            values = self.values(create_missing=True, cells=[{"sphere": "0.5", "cylinder": "0", "quantity": 1}])
            with patch("inventory.services.uuid.uuid4", return_value=fixed), self.assertRaises(ValidationError):
                receive_matrix(self.owner.pk, **values)
            self.assertFalse(StockBalance.objects.exists())
            self.assertFalse(StockReceipt.objects.exists())

    def test_supported_stock_kinds_and_nonstock_exclusions(self):
        cases = [("frame", "piece", {"color": "black", "eye_size": 52, "bridge": 18, "temple": 140}),
            ("accessory", "piece", {}), ("device", "piece", {"specification": "V1"}),
            ("contact_lens", "box", {"material": "Hydrogel", "diameter": "14", "base_curve": "8.6", "sphere": "0", "pack_size": 30, "replacement": "monthly"}),
            ("service", "service", {"description": "Delivery"}),
            ("rx_lens", "piece", {k: v for k, v in fixtures.SPECS.items() if k not in {"sphere", "cylinder"}})]
        with tenant_context(self.a):
            for kind, unit, specs in cases:
                product = create_product(self.owner.pk, code_value=kind.upper(), name="Synthetic label product", kind=kind)
                variant = create_variant(self.owner.pk, product_id=product.pk, sku="LBL-" + kind.upper(), unit=unit, base_price="10", specifications=specs)
                if kind in {"service", "rx_lens"}:
                    with self.assertRaises(Variant.DoesNotExist):
                        label_preview(self.owner.pk, variant_id=variant.pk, copies=1)
                else:
                    self.assertEqual(label_preview(self.reader.pk, variant_id=variant.pk, copies=1)["code_value"], variant.sku)

    def test_http_permissions_revocation_foreign_company_and_csrf(self):
        self.login("reader")
        self.assertEqual(self.get(self.path).status_code, 200)
        response = self.post(self.path, {"copies": 2, "layout": "auto"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="barcode-label"', count=2)
        self.assertIn("no-store", response.headers["Cache-Control"])
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r08.test")
        self.assertEqual(foreign.get(self.path, HTTP_HOST="b.r08.test").status_code, 404)
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(self.path, {"copies": 1, "layout": "auto"}, HTTP_HOST="a.r08.test").status_code, 403)
        with tenant_context(self.a):
            assignment = RoleAssignment.objects.get(user=self.reader, role_id="catalog_reader")
            revoke_role(self.owner.pk, assignment_id=assignment.pk)
            type(self.reader).objects.filter(pk=self.reader.pk).update(is_superuser=True)
        self.assertEqual(self.post(self.path, {"copies": 1, "layout": "auto"}).status_code, 403)

    def test_invalid_post_and_inactive_variant_do_not_return_print_document(self):
        response = self.post(self.path, {"copies": 121, "layout": "auto"})
        self.assertEqual(response.status_code, 422)
        self.assertNotContains(response, 'class="barcode-label"', status_code=422)
        with tenant_context(self.a):
            Variant.objects.filter(pk=self.template.pk).update(active=False)
        self.assertEqual(self.get(self.path).status_code, 404)
