from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
import uuid
from psycopg import sql
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.test import Client, SimpleTestCase, TransactionTestCase, override_settings
from django.utils import timezone
from django_tenants.utils import tenant_context, schema_context
from access.models import Branch
from access.services import create_branch, create_member, assign_role, revoke_role, set_branch_active
from directory.provisioning import provision_company
from directory.db_roles import grant_tenant_runtime
from clinical.services import create_customer
from catalog import services
from catalog.models import Product, Variant, PriceRule
from catalog.specifications import canonical_specs, money

PASSWORD = "Synthetic-Catalog-2026!"
FRAME = {"color": "Black", "eye_size": 52, "bridge": 18, "temple": 140}
LENS = {"material": "Resin", "index": "1.60", "diameter": "70", "design": "single", "coatings": "AR, UV"}
CONTACT = {"material": "Hydrogel", "diameter": "14.2", "base_curve": "8.6", "sphere": "-1.00", "pack_size": 30, "replacement": "daily"}


class SpecificationTests(SimpleTestCase):
    def test_all_optical_and_basic_variant_types(self):
        cases = [("frame", FRAME, "piece"), ("stock_lens", {**LENS, "sphere": "0"}, "piece"), ("rx_lens", LENS, "pair"), ("contact_lens", CONTACT, "box"), ("accessory", {}, "piece"), ("device", {"specification": "V2"}, "piece"), ("service", {"description": "Adjustment"}, "service")]
        for kind, specs, unit in cases:
            with self.subTest(kind=kind):
                packed, fingerprint = canonical_specs(kind, specs, unit)
                self.assertEqual(packed["kind"], kind)
                self.assertEqual(len(fingerprint), 64)

    def test_canonical_coatings_text_and_signed_zero_are_identical(self):
        first = canonical_specs("stock_lens", {**LENS, "sphere": "-0.00", "cylinder": "", "coatings": "UV, AR, ar"}, "piece")
        second = canonical_specs("stock_lens", {**LENS, "material": "  RESIN ", "sphere": "0", "cylinder": "0.00", "coatings": ["ar", "uv"]}, "piece")
        self.assertEqual(first, second)
        self.assertEqual(first[0]["values"]["sphere"], "0.00")

    def test_invalid_shapes_fields_precision_and_patient_powers_on_rx_rejected(self):
        cases = [("frame", {**FRAME, "eye_size": 200}, "piece"), ("frame", {**FRAME, "color": []}, "piece"), ("rx_lens", {**LENS, "sphere": "1"}, "piece"), ("stock_lens", {**LENS, "sphere": "0.10"}, "piece"), ("stock_lens", {**LENS, "sphere": float("nan")}, "piece"), ("rx_lens", {**LENS, "coatings": [1]}, "piece"), ("frame", FRAME, "box")]
        for kind, specs, unit in cases:
            with self.subTest(specs=specs), self.assertRaises(ValidationError):
                canonical_specs(kind, specs, unit)

    def test_contact_toric_axis_and_package_validation(self):
        for values in ({"cylinder": "-1.25"}, {"axis": 90}, {"cylinder": "-1.25", "axis": 181}, {"pack_size": 0}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                canonical_specs("contact_lens", {**CONTACT, **values}, "box")
        self.assertEqual(canonical_specs("contact_lens", {**CONTACT, "cylinder": "-1.25", "axis": 0}, "box")[0]["values"]["axis"], 0)

    def test_unit_is_part_of_identity_without_implicit_conversion(self):
        self.assertNotEqual(canonical_specs("rx_lens", LENS, "piece")[1], canonical_specs("rx_lens", LENS, "pair")[1])

    def test_money_and_quantity_never_silently_round_or_accept_float(self):
        self.assertEqual(money("0"), Decimal("0.00"))
        for value in ("1.001", "-1", "NaN", "Infinity", 1.2, True):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                money(value)
        for value in (0, "1.5", "1000001", True, 1.0):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                services.quantity(value)


@override_settings(ALLOWED_HOSTS=["a.r07.test", "b.r07.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CatalogTests(TransactionTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        self.a = provision_company(name="Synthetic Catalog A", domain="a.r07.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        self.b = provision_company(name="Synthetic Catalog B", domain="b.r07.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        self.day = timezone.localdate()
        with tenant_context(self.a):
            self.owner = get_user_model().objects.get(username="owner")
            self.main = Branch.objects.get(code="MAIN")
            self.other = create_branch(self.owner.pk, code="B02", name="Other branch")
            self.reader = create_member(self.owner.pk, username="reader", password=PASSWORD)
            self.reader_grant = assign_role(self.owner.pk, user_id=self.reader.pk, role_code="catalog_reader")
            self.cashier = create_member(self.owner.pk, username="cashier", password=PASSWORD)
            assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="cashier", branch_id=self.main.pk)
            assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="catalog_reader")
            self.customer = create_customer(self.owner.pk, branch_id=self.main.pk, first_name="Synthetic customer")
            self.product = services.create_product(self.owner.pk, code_value="FRAME-01", name="Synthetic frame", kind="frame")
            self.variant = services.create_variant(self.owner.pk, product_id=self.product.pk, sku="FR-52-BLACK", barcode="00123456", unit="piece", base_price="100.00", specifications=FRAME)
        self.login()

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def login(self, username="owner"):
        self.client = Client()
        self.assertEqual(self.client.post("/auth/login/", {"username": username, "password": PASSWORD}, HTTP_HOST="a.r07.test").status_code, 302)

    def get(self, path):
        return self.client.get(path, HTTP_HOST="a.r07.test")

    def post(self, path, data):
        return self.client.post(path, data, HTTP_HOST="a.r07.test")

    def rule(self, **kwargs):
        values = {"variant_id": self.variant.pk, "valid_from": self.day, "unit_price": "80.00"}
        values.update(kwargs)
        return services.create_price_rule(self.owner.pk, **values)

    def quote(self, **kwargs):
        values = {"variant_id": self.variant.pk, "branch_id": self.main.pk}
        values.update(kwargs)
        return services.quote_price(self.owner.pk, **values)

    def test_sku_barcode_and_canonical_specs_unique_per_company(self):
        with tenant_context(self.a):
            for values in ({"sku": "fr-52-black", "barcode": "", "specifications": {**FRAME, "color": "blue"}}, {"sku": "NEW", "barcode": "00123456", "specifications": {**FRAME, "color": "blue"}}, {"sku": "OTHER", "barcode": "", "specifications": {**FRAME, "color": " BLACK "}}):
                with self.subTest(values=values), self.assertRaises(ValidationError):
                    services.create_variant(self.owner.pk, product_id=self.product.pk, unit="piece", base_price="10.00", **values)
            self.assertEqual(Variant.objects.count(), 1)
            self.assertEqual(self.variant.barcode, "00123456")
            for kind, specs, unit in (("stock_lens", {**LENS, "sphere": "0"}, "piece"), ("rx_lens", LENS, "pair"), ("contact_lens", CONTACT, "box")):
                product = services.create_product(self.owner.pk, code_value=kind.upper(), name=kind, kind=kind)
                variant = services.create_variant(self.owner.pk, product_id=product.pk, sku=kind.upper(), unit=unit, base_price="19.99", specifications=specs)
                variant.refresh_from_db()
                self.assertEqual(variant.specifications["kind"], kind)
                self.assertEqual(self.quote(variant_id=variant.pk, count=3)["total"], "59.97")
        with tenant_context(self.b):
            owner = get_user_model().objects.get(username="owner")
            product = services.create_product(owner.pk, code_value="FRAME-01", name="Independent", kind="frame")
            self.assertIsNotNone(services.create_variant(owner.pk, product_id=product.pk, sku="FR-52-BLACK", barcode="00123456", unit="piece", base_price="10", specifications=FRAME))

    def test_database_constraints_for_variant_and_price_rule(self):
        with tenant_context(self.a):
            for changes in ({"base_price": -1},):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Variant.objects.filter(pk=self.variant.pk).update(**changes)
            clone = Variant.objects.get(pk=self.variant.pk)
            clone.pk, clone.sku, clone.barcode = uuid.uuid4(), "CLONE", None
            with self.assertRaises(IntegrityError), transaction.atomic():
                clone.save(force_insert=True)
            rule = self.rule()
            for changes in ({"unit_price": -1}, {"min_quantity": 0}, {"valid_until": self.day - timedelta(days=1)}, {"customer_id": self.customer.pk}, {"channel": "invalid"}):
                with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                    PriceRule.objects.filter(pk=rule.pk).update(**changes)
            duplicate = PriceRule.objects.get(pk=rule.pk)
            duplicate.pk = uuid.uuid4()
            with self.assertRaises(IntegrityError), transaction.atomic():
                duplicate.save(force_insert=True)

    def test_reader_cannot_manage_even_with_superuser_flags(self):
        self.login("reader")
        self.assertEqual(self.get("/catalog/").status_code, 200)
        self.assertNotContains(self.get("/catalog/"), "إضافة منتج")
        self.assertEqual(self.post("/catalog/new/", {"code_value": "BAD", "name": "Bad", "kind": "frame"}).status_code, 403)
        self.assertEqual(self.get(f"/catalog/variants/{self.variant.pk}/prices/new/").status_code, 403)
        with tenant_context(self.a):
            self.reader.is_superuser = self.reader.is_staff = True
            self.reader.save(update_fields=["is_superuser", "is_staff"])
        self.assertEqual(self.get(f"/catalog/variants/{self.variant.pk}/edit/").status_code, 403)

    def test_company_and_public_isolation_and_foreign_identifiers(self):
        with schema_context("public"), connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'catalog_%'")
            self.assertEqual(cursor.fetchall(), [])
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="b.r07.test")
        for path in (f"/catalog/products/{self.product.pk}/", f"/catalog/variants/{self.variant.pk}/", f"/catalog/variants/{self.variant.pk}/quote/"):
            self.assertEqual(foreign.get(path, HTTP_HOST="b.r07.test").status_code, 404)
        self.assertEqual(Client().get("/catalog/", HTTP_HOST="a.r07.test").status_code, 403)

    def test_search_by_barcode_sku_type_and_pagination_has_correct_counts(self):
        with tenant_context(self.a):
            services.create_variant(self.owner.pk, product_id=self.product.pk, sku="FR-53-BLACK", unit="piece", base_price="110", specifications={**FRAME, "eye_size": 53})
            Product.objects.bulk_create([Product(code=f"P{i}", name=f"Synthetic {i}", kind="accessory", created_by=self.owner) for i in range(23)])
        response = self.get("/catalog/?q=FR-5")
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(response.context["page_obj"][0].variant_count, 2)
        self.assertEqual(self.get("/catalog/?q=00123456").context["page_obj"].paginator.count, 1)
        self.assertEqual(len(self.get("/catalog/?page=2").context["page_obj"]), 4)
        self.assertEqual(self.get("/catalog/?kind=contact_lens").context["page_obj"].paginator.count, 0)

    def test_variant_identity_immutable_http_and_stale_updates_rejected(self):
        response = self.post(f"/catalog/variants/{self.variant.pk}/edit/", {"base_price": "120.00", "active": "true", "expected_version": 1, "sku": "FORGED", "unit": "pair"})
        self.assertEqual(response.status_code, 302)
        with tenant_context(self.a):
            self.variant.refresh_from_db()
            self.assertEqual(self.variant.sku, "FR-52-BLACK")
            self.assertEqual(self.variant.unit, "piece")
            with self.assertRaises(ValidationError):
                services.update_variant(self.owner.pk, variant_id=self.variant.pk, expected_version=1, base_price="1", active=True)
            services.update_product(self.owner.pk, product_id=self.product.pk, expected_version=1, name="Updated", brand="", model="", active=True)
            with self.assertRaises(ValidationError):
                services.update_product(self.owner.pk, product_id=self.product.pk, expected_version=1, name="Stale", brand="", model="", active=True)

    def test_price_precedence_quantity_and_zero_special_price(self):
        with tenant_context(self.a):
            self.assertEqual(self.quote()["unit_price"], "100.00")
            self.rule(unit_price="90")
            self.rule(min_quantity=10, unit_price="70")
            self.assertEqual(self.quote(count=10)["unit_price"], "70.00")
            self.rule(branch_id=self.main.pk, unit_price="85")
            self.assertEqual(self.quote(count=10)["unit_price"], "85.00")
            self.rule(branch_id=self.main.pk, customer_id=self.customer.pk, unit_price="0")
            quoted = self.quote(customer_id=self.customer.pk, count=10)
            self.assertEqual(quoted["unit_price"], "0.00")
            self.assertEqual(quoted["total"], "0.00")
            self.assertEqual(quoted["source"], "customer")

    def test_channels_date_endpoints_and_exact_decimal_totals(self):
        with tenant_context(self.a):
            self.rule(valid_from=self.day, valid_until=self.day + timedelta(days=2), unit_price="19.99", channel="wholesale")
            self.assertEqual(self.quote(channel="retail")["source"], "base")
            self.assertEqual(self.quote(channel="wholesale", count=3, as_of=self.day + timedelta(days=2))["total"], "59.97")
            self.assertEqual(self.quote(channel="wholesale", as_of=self.day - timedelta(days=1))["source"], "base")
            self.assertEqual(self.quote(channel="wholesale", as_of=self.day + timedelta(days=3))["source"], "base")

    def test_overlap_same_scope_rejected_disjoint_period_and_tiers_allowed(self):
        with tenant_context(self.a):
            self.rule(valid_until=self.day + timedelta(days=2))
            with self.assertRaises(ValidationError):
                self.rule(valid_from=self.day + timedelta(days=2), valid_until=self.day + timedelta(days=5))
            self.rule(valid_from=self.day + timedelta(days=3), valid_until=self.day + timedelta(days=5))
            self.rule(min_quantity=5)
            self.assertEqual(PriceRule.objects.count(), 3)

    def test_concurrent_overlapping_rules_accept_one(self):
        def create(index):
            connections.close_all()
            try:
                with tenant_context(self.a):
                    try:
                        self.rule(valid_from=self.day + timedelta(days=index), valid_until=self.day + timedelta(days=5))
                        return "saved"
                    except ValidationError:
                        return "rejected"
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(create, range(2))), ["saved", "rejected"])
        with tenant_context(self.a):
            self.assertEqual(PriceRule.objects.count(), 1)

    def test_customer_branch_and_quote_permissions_are_live(self):
        with tenant_context(self.a):
            with self.assertRaises(PermissionDenied):
                services.quote_price(self.reader.pk, variant_id=self.variant.pk, branch_id=self.main.pk)
            with self.assertRaises(PermissionDenied):
                services.quote_price(self.cashier.pk, variant_id=self.variant.pk, branch_id=self.other.pk)
            with self.assertRaises(PermissionDenied):
                self.quote(branch_id=self.other.pk, customer_id=self.customer.pk)
            with self.assertRaises(ValidationError):
                self.rule(customer_id=self.customer.pk)
            with self.assertRaises(PermissionDenied):
                self.rule(branch_id=self.other.pk, customer_id=self.customer.pk)
            self.assertEqual(services.quote_price(self.cashier.pk, variant_id=self.variant.pk, branch_id=self.main.pk)["source"], "base")

    def test_rule_disabled_without_deletion_and_snapshot_does_not_change(self):
        with tenant_context(self.a):
            rule = self.rule(unit_price="75")
            snapshot = self.quote(count=2)
            services.disable_price_rule(self.owner.pk, rule_id=rule.pk)
            self.assertEqual(self.quote()["unit_price"], "100.00")
            self.assertEqual(PriceRule.objects.count(), 1)
            self.assertEqual(snapshot["unit_price"], "75.00")
            self.assertEqual(snapshot["total"], "150.00")
            self.assertEqual(snapshot["company_id"], str(self.a.pk))
            services.update_variant(self.owner.pk, variant_id=self.variant.pk, expected_version=1, base_price="130", active=False)
            with self.assertRaises(Variant.DoesNotExist):
                self.quote()
            self.assertEqual(snapshot["unit_price"], "75.00")

    def test_ambiguous_legacy_or_direct_database_rules_fail_closed(self):
        with tenant_context(self.a):
            first = self.rule()
            PriceRule.objects.create(variant=self.variant, channel="retail", valid_from=self.day - timedelta(days=1), unit_price=1, min_quantity=1, created_by=self.owner)
            with self.assertRaises(ValidationError):
                self.quote()

    def test_invalid_price_scope_form_and_refresh_have_no_side_effect(self):
        url = f"/catalog/variants/{self.variant.pk}/prices/new/"
        data = {"branch_id": self.main.pk, "channel": "retail", "min_quantity": 1, "unit_price": "25.00", "valid_from": self.day, "refresh": "customers"}
        self.assertEqual(self.post(url, data).status_code, 200)
        with tenant_context(self.a):
            self.assertEqual(PriceRule.objects.count(), 0)
        invalid = self.post(url, {**data, "refresh": "", "branch_id": "invalid-uuid"})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(self.post(url, {**data, "refresh": "", "customer_id": self.customer.pk}).status_code, 302)

    def test_revocation_and_disabled_branch_and_product_are_effective(self):
        self.login("reader")
        with tenant_context(self.a):
            revoke_role(self.owner.pk, assignment_id=self.reader_grant.pk)
        self.assertEqual(self.get("/catalog/").status_code, 403)
        with tenant_context(self.a):
            set_branch_active(self.owner.pk, branch_id=self.main.pk, active=False)
            with self.assertRaises(PermissionDenied):
                self.quote()
            services.update_product(self.owner.pk, product_id=self.product.pk, expected_version=1, name=self.product.name, brand="", model="", active=False)
            with self.assertRaises(Product.DoesNotExist):
                services.create_variant(self.owner.pk, product_id=self.product.pk, sku="NEW", unit="piece", base_price="1", specifications=FRAME)

    def test_runtime_grants_protect_identity_and_rule_content_but_allow_price_and_disable(self):
        role = "r07_probe_" + uuid.uuid4().hex
        with tenant_context(self.a):
            rule = self.rule()
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
            try:
                for statement in ("UPDATE catalog_product SET code=code WHERE false", "UPDATE catalog_variant SET specifications=specifications WHERE false", "UPDATE catalog_variant SET sku=sku WHERE false", "UPDATE catalog_pricerule SET unit_price=unit_price WHERE false", "DELETE FROM catalog_variant WHERE false", "DELETE FROM catalog_pricerule WHERE false"):
                    with self.subTest(statement=statement), self.assertRaises(ProgrammingError) as error, transaction.atomic():
                        with connection.cursor() as cursor:
                            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                            cursor.execute(statement)
                    self.assertEqual(getattr(error.exception.__cause__, "sqlstate", None), "42501")
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    cursor.execute("UPDATE catalog_variant SET base_price=base_price WHERE false")
                    cursor.execute("UPDATE catalog_pricerule SET active=active WHERE false")
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
