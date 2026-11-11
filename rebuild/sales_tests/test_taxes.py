from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from datetime import date
import uuid
from psycopg import sql
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, override_settings, Client
from django_tenants.utils import tenant_context
from access.services import assign_role, revoke_role, revoke_branch_access, create_branch
from access.models import AuditEvent
from catalog.services import create_product, create_variant, update_variant
from catalog.models import Variant
from clinical.models import CustomerBranchAccess
from clinical.services import create_customer
from directory.db_roles import grant_tenant_runtime
from finance.models import JournalEntry
from finance.services import save_fiscal_profile
from finance_tests.test_fiscal import data
from inventory.models import StockMovement
from sales.models import TaxTreatmentRevision, TaxQuote
from sales.taxes import revise_treatment, create_tax_quote, quotes_for
from workspace_tests import test_workspace as fixtures
from catalog_tests import test_catalog as catalog_fixture


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class RetailTaxTests(TransactionTestCase):
    login = fixtures.WorkspaceTests.login
    get = fixtures.WorkspaceTests.get
    post = fixtures.WorkspaceTests.post

    def setUp(self):
        fixtures.WorkspaceTests.setUp(self)
        with tenant_context(self.a):
            self.other = create_branch(self.owner.pk, code="OTHER", name="Synthetic hidden")
            self.catalog_grant = assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="catalog_reader")
            self.product = create_product(self.owner.pk, code_value="TAX-FRAME", name="Synthetic taxed frame", kind="frame")
            self.variant = create_variant(self.owner.pk, product_id=self.product.pk, sku="TAX-01", unit="piece", base_price="100", specifications=catalog_fixture.FRAME)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def profile(self, **changes):
        return save_fiscal_profile(self.owner.pk, data=data(**changes), expected_version=0, operation_key=uuid.uuid4(), reason="Synthetic setup")

    def revision(self, **changes):
        actor = changes.pop("actor_id", self.owner.pk)
        return revise_treatment(actor, **(dict(variant_id=self.variant.pk, expected_version=0, valid_from="2026-11-11", state="reviewed", category="S", basis="Synthetic classification review", operation_key=uuid.uuid4(), reason="Synthetic review") | changes))

    def quote(self, **changes):
        actor = changes.pop("actor_id", self.owner.pk)
        return create_tax_quote(actor, **(dict(branch_id=self.branch.pk, as_of="2026-11-11", lines=[dict(sku="tax-01", quantity=1, price_basis="gross", unit_amount="115", discount_kind="amount", discount_value="0")], operation_key=uuid.uuid4(), reason="Synthetic quote") | changes))

    def test_unknown_registration_classification_block_and_effective_history(self):
        with tenant_context(self.a):
            with self.assertRaises(ValidationError):
                self.quote()
            self.profile()
            with self.assertRaises(ValidationError):
                self.quote()
            first = self.revision()
            original = self.quote()
            self.revision(expected_version=1, valid_from="2026-11-12", state="blocked", category="")
            self.assertEqual(self.quote().payload["sources"][0]["tax_revision"]["id"], str(first.pk))
            with self.assertRaises(ValidationError):
                self.quote(as_of="2026-11-12")
            with self.assertRaises(ValidationError):
                self.revision(expected_version=2, valid_from="2026-11-11")
            self.revision(expected_version=2, valid_from="2026-11-12")
            self.assertEqual(self.quote(as_of="2026-11-12").payload["sources"][0]["tax_revision"]["version"], 3)
            original.refresh_from_db()
            self.assertEqual(original.payload["sources"][0]["tax_revision"]["version"], 1)

    def test_prices_snapshots_registration_and_no_posting_side_effects(self):
        with tenant_context(self.a):
            self.profile()
            self.revision()
            quote = self.quote()
            catalog = self.quote(lines=[dict(sku="TAX-01", quantity=1, price_basis="catalog_net", unit_amount=None, discount_kind="amount", discount_value="0")])
            self.assertEqual(quote.payable, catalog.payable)
            before = quote.payload
            update_variant(self.owner.pk, variant_id=self.variant.pk, expected_version=1, base_price="200", active=True)
            save_fiscal_profile(self.owner.pk, data=data(city="Changed synthetic city"), expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic change")
            quote.refresh_from_db()
            self.assertEqual(quote.payload, before)
            self.assertFalse(quote.payload["can_issue_invoice"] or quote.payload["can_submit_to_zatca"])
            self.assertEqual((JournalEntry.objects.count(), StockMovement.objects.count()), (0, 0))
            self.variant.refresh_from_db()
            self.assertEqual(str(self.variant.base_price), "200.00")

    def test_nonregistered_needs_no_invented_tax_and_unknown_still_blocks(self):
        with tenant_context(self.a):
            self.profile(registration_status="not_registered", vat_number="")
            quote = self.quote()
            self.assertEqual((str(quote.vat), str(quote.payable), quote.payload["vat_breakdown"]), ("0.00", "115.00", []))
            save_fiscal_profile(self.owner.pk, data=data(registration_status="unknown", vat_number=""), expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic unknown")
            with self.assertRaises(ValidationError):
                self.quote()

    def test_idempotency_conflict_stale_revision_and_reauthorization(self):
        with tenant_context(self.a):
            self.profile()
            revision_key, quote_key = uuid.uuid4(), uuid.uuid4()
            first = self.revision(operation_key=revision_key)
            self.assertEqual(self.revision(operation_key=revision_key).pk, first.pk)
            for changes in ({"operation_key": revision_key, "basis": "Different"}, {"expected_version": 0}):
                with self.assertRaises(ValidationError):
                    self.revision(**changes)
            quote = self.quote(actor_id=self.cashier.pk, operation_key=quote_key)
            self.assertEqual(self.quote(actor_id=self.cashier.pk, operation_key=quote_key).pk, quote.pk)
            with self.assertRaises(ValidationError):
                self.quote(actor_id=self.cashier.pk, operation_key=quote_key, document_discount_value="1")
            revoke_role(self.owner.pk, assignment_id=self.catalog_grant.pk)
            self.cashier.is_superuser = True
            self.cashier.save(update_fields=["is_superuser"])
            with self.assertRaises(PermissionDenied):
                self.quote(actor_id=self.cashier.pk, operation_key=quote_key)
            with self.assertRaises(PermissionDenied):
                self.revision(actor_id=self.cashier.pk, operation_key=revision_key)

    def test_branch_customer_scope_and_cross_tenant_absence(self):
        with tenant_context(self.a):
            self.profile()
            self.revision()
            public_quote = self.quote()
            hidden = self.quote(branch_id=self.other.pk)
            customer = create_customer(self.owner.pk, branch_id=self.branch.pk, first_name="Synthetic customer", identifier="TAX-CUST")
            personal = self.quote(customer_id=customer.pk)
            self.assertEqual(set(quotes_for(self.cashier.pk).values_list("pk", flat=True)), {public_quote.pk, personal.pk})
            with self.assertRaises(PermissionDenied):
                self.quote(actor_id=self.cashier.pk, branch_id=self.other.pk)
            CustomerBranchAccess.objects.filter(customer=customer).delete()
            self.assertEqual(list(quotes_for(self.cashier.pk).values_list("pk", flat=True)), [public_quote.pk])
            with self.assertRaises(PermissionDenied):
                self.quote(customer_id=customer.pk, operation_key=personal.operation_key)
            revoke_branch_access(self.owner.pk, user_id=self.cashier.pk, branch_id=self.branch.pk)
            self.assertFalse(quotes_for(self.cashier.pk).exists())
        with tenant_context(self.b):
            self.assertEqual((TaxQuote.objects.count(), TaxTreatmentRevision.objects.count()), (0, 0))
            with self.assertRaises(PermissionDenied):
                self.quote()
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            for table in ("sales_taxquote", "sales_taxtreatmentrevision"):
                cursor.execute("SELECT to_regclass(%s)", ["public." + table])
                self.assertIsNone(cursor.fetchone()[0])

    def test_audit_failure_rolls_back_both_writes(self):
        with tenant_context(self.a):
            self.profile()
            count = AuditEvent.objects.count()
            with patch("sales.taxes.audit", side_effect=RuntimeError("Synthetic audit failure")), self.assertRaises(RuntimeError):
                self.revision()
            self.assertFalse(TaxTreatmentRevision.objects.exists())
            self.assertEqual(AuditEvent.objects.count(), count)
            self.revision()
            count = AuditEvent.objects.count()
            with patch("sales.taxes.audit", side_effect=RuntimeError("Synthetic audit failure")), self.assertRaises(RuntimeError):
                self.quote()
            self.assertFalse(TaxQuote.objects.exists())
            self.assertEqual(AuditEvent.objects.count(), count)

    def test_invalid_sources_dates_and_row_limits_leave_no_quote(self):
        with tenant_context(self.a):
            self.profile()
            self.revision()
            valid = dict(sku="TAX-01", quantity=1, price_basis="gross", unit_amount="115", discount_kind="amount", discount_value="0")
            for changes in ({"as_of": "2026-11-10"}, {"as_of": "2019-01-01"}, {"lines": []}, {"lines": [valid] * 41},
                {"lines": [valid | {"sku": "MISSING"}]}, {"lines": [valid | {"price_basis": "catalog_net"}]}, {"lines": [valid | {"quantity": True}]},
                {"lines": [valid | {"unit_amount": "NaN"}]}, {"lines": [valid | {"extra": "forged"}]}):
                with self.subTest(changes=changes), self.assertRaises(ValidationError):
                    self.quote(**changes)
            self.assertFalse(TaxQuote.objects.exists())
            update_variant(self.owner.pk, variant_id=self.variant.pk, expected_version=1, base_price="100", active=False)
            with self.assertRaises(ValidationError):
                self.quote()

    def test_classification_http_append_and_forged_branch_rejected(self):
        path = f"/sales/taxes/{self.variant.pk}/"
        response = self.get(path)
        self.assertEqual(response.status_code, 200)
        values = dict(valid_from="2026-11-11", state="reviewed", category="S", reason_code="", exception_text="", basis="Synthetic HTTP classification", reason="Synthetic review", expected_version="0", operation_key=str(uuid.uuid4()))
        self.assertEqual(self.post(path, values).status_code, 302)
        self.assertEqual(self.post(path, values | {"operation_key": str(uuid.uuid4())}).status_code, 422)
        with tenant_context(self.a):
            self.assertEqual(TaxTreatmentRevision.objects.count(), 1)
        self.login("cashier")
        self.assertEqual(self.post(path, values).status_code, 403)
        form = self.get("/sales/quotes/new/")
        self.assertContains(form, f'value="{self.branch.pk}"')
        self.assertNotContains(form, f'value="{self.other.pk}"')

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

    def test_concurrent_revision_and_duplicate_quote(self):
        revisions = self.parallel([lambda: self.revision()] * 2)
        self.assertEqual(sum(item is not None for item in revisions), 1)
        with tenant_context(self.a):
            self.profile()
        key = uuid.uuid4()
        quotes = self.parallel([lambda: self.quote(operation_key=key)] * 2)
        self.assertIsNotNone(quotes[0])
        self.assertEqual(quotes[0], quotes[1])
        with tenant_context(self.a):
            self.assertEqual((TaxTreatmentRevision.objects.count(), TaxQuote.objects.count()), (1, 1))

    def test_runtime_immutability_and_database_constraints(self):
        with tenant_context(self.a):
            self.profile()
            revision = self.revision()
            quote = self.quote()
            for updates in ({"rate": 5}, {"state": "blocked"}, {"version": 0}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    TaxTreatmentRevision.objects.filter(pk=revision.pk).update(**updates)
            with self.assertRaises(IntegrityError), transaction.atomic():
                TaxQuote.objects.filter(pk=quote.pk).update(payable="1")
            role = "tax_test_" + uuid.uuid4().hex[:16]
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
            try:
                with connection.cursor() as cursor:
                    grant_tenant_runtime(cursor, self.a.schema_name, role)
                    cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    self.assertEqual(self.revision(expected_version=1).version, 2)
                    self.assertEqual(str(self.quote().payable), "115.00")
                for table in ("sales_taxquote", "sales_taxtreatmentrevision"):
                    for statement in (f"UPDATE {table} SET reason=reason WHERE false", f"DELETE FROM {table} WHERE false"):
                        with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                            cursor.execute(statement)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_additive_migration_preserves_existing_catalog(self):
        with tenant_context(self.a):
            before = list(Variant.objects.values())
            MigrationExecutor(connection).migrate([("sales", "0003_shift_guards")])
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes("sales"))
            self.assertEqual(list(Variant.objects.values()), before)
            self.assertFalse(TaxQuote.objects.exists())

    def test_http_forms_scope_csrf_and_saved_snapshot(self):
        with tenant_context(self.a):
            self.profile()
            self.revision()
        form = self.get("/sales/quotes/new/")
        self.assertEqual(form.status_code, 200)
        payload = {"branch_id": str(self.branch.pk), "as_of": "2026-11-11", "document_discount_kind": "amount", "document_discount_value": "11.50", "reason": "Synthetic HTTP", "operation_key": str(uuid.uuid4()),
            "lines-TOTAL_FORMS": "1", "lines-INITIAL_FORMS": "0", "lines-0-sku": "TAX-01", "lines-0-quantity": "1", "lines-0-price_basis": "gross", "lines-0-unit_amount": "115", "lines-0-discount_kind": "percent", "lines-0-discount_value": "10"}
        result = self.post("/sales/quotes/new/", payload)
        self.assertEqual(result.status_code, 302)
        detail = self.get(result.url)
        self.assertContains(detail, "92.00")
        self.assertContains(detail, "12.00")
        self.assertEqual(self.post(result.url, {}).status_code, 405)
        self.login("cashier")
        self.assertEqual(self.get("/sales/taxes/").status_code, 403)
        self.assertEqual(self.get(result.url).status_code, 200)
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r05.test")
        self.assertEqual(foreign.get(result.url, HTTP_HOST="b.r05.test").status_code, 404)
        csrf = Client(enforce_csrf_checks=True)
        csrf.cookies = self.client.cookies
        self.assertEqual(csrf.post("/sales/quotes/new/", payload, HTTP_HOST="a.r05.test").status_code, 403)
