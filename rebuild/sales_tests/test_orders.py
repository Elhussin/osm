import uuid
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from psycopg import sql
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase, override_settings, Client
from django_tenants.utils import tenant_context
from django.utils import timezone
from access.authorization import allowed
from access.services import assign_role, revoke_role, set_member_active
from clinical.services import create_customer, record_prescription, correct_prescription, update_customer
from clinical.models import CustomerBranchAccess
from clinical_tests.test_clinical import measurements, image_upload
from catalog.services import update_variant
from catalog.services import create_product, create_variant
from catalog_tests.test_catalog import CONTACT, LENS
from directory.db_roles import grant_tenant_runtime
from finance.setup_services import create_account
from finance.models import JournalEntry
from inventory.receiving import receive_stock
from inventory.reservations import reserve_stock, change_reservation
from inventory.models import StockBalance, StockReservation, StockMovement
from sales.registers import create_register
from sales.shifts import open_shift, act_on_shift
from sales.models import SaleOrder, OrderRevision, OrderEvent, OrderHold, TaxQuote
from sales.orders import save_order, act_on_order, orders_for
from sales_tests import test_taxes as fixtures


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CashOrderTests(TransactionTestCase):
    login = fixtures.RetailTaxTests.login
    get = fixtures.RetailTaxTests.get
    post = fixtures.RetailTaxTests.post
    profile = fixtures.RetailTaxTests.profile
    revision = fixtures.RetailTaxTests.revision
    parallel = fixtures.RetailTaxTests.parallel

    def setUp(self):
        fixtures.RetailTaxTests.setUp(self)
        with tenant_context(self.a):
            self.profile()
            self.revision()
            self.customer = create_customer(self.owner.pk, branch_id=self.branch.pk, first_name="Synthetic order customer")
            cash = create_account(self.owner.pk, code="1109", name="Synthetic order cash", kind="asset", normal_side="debit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic setup").account
            register = create_register(self.owner.pk, branch_id=self.branch.pk, code="SALE", name="صندوق البيع التجريبي", cash_account_code=cash.code, operation_key=uuid.uuid4(), reason="Synthetic setup").register
            self.shift = open_shift(self.cashier.pk, register_id=register.pk, opening_cash="100", operation_key=uuid.uuid4(), reason="Synthetic open").shift
            receive_stock(self.owner.pk, branch_id=self.branch.pk, variant_id=self.variant.pk, quantity=2, operation_key=uuid.uuid4(), reason="Synthetic stock")

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def quote(self, **changes):
        return fixtures.RetailTaxTests.quote(self, **(dict(as_of=timezone.localdate()) | changes))

    def save(self, **changes):
        actor = changes.pop("actor_id", self.cashier.pk)
        if "quote_id" not in changes:
            changes["quote_id"] = self.quote(customer_id=self.customer.pk, as_of=timezone.localdate()).pk
        return save_order(actor, **(dict(shift_id=self.shift.pk, positions=[None], operation_key=uuid.uuid4(), reason="Synthetic order") | changes))

    def action(self, order, action="confirm", **changes):
        actor = changes.pop("actor_id", self.cashier.pk)
        order.refresh_from_db()
        return act_on_order(actor, **(dict(order_id=order.pk, action=action, expected_version=order.version, operation_key=uuid.uuid4(), reason="Synthetic action") | changes))

    def test_cashier_confirm_and_cancel_without_general_inventory_permission(self):
        with tenant_context(self.a):
            draft = self.save().order
            self.assertEqual(StockBalance.objects.get().reserved, 0)
            self.assertFalse(allowed(self.cashier.pk, "stock.reserve", [self.branch.pk]))
            with self.assertRaises(PermissionDenied):
                reserve_stock(self.cashier.pk, branch_id=self.branch.pk, variant_id=self.variant.pk, quantity=1, operation_key=uuid.uuid4(), reason="Denied direct")
            self.action(draft)
            self.assertEqual(StockBalance.objects.get().reserved, 1)
            hold = OrderHold.objects.select_related("reservation").get()
            self.assertEqual((hold.reservation.held, hold.position), (1, 1))
            for kind in ("cancel", "issue", "release", "reverse_issue"):
                with self.assertRaises(ValidationError):
                    change_reservation(self.owner.pk, reservation_id=hold.reservation_id, kind=kind, expected_version=1, quantity=1, operation_key=uuid.uuid4(), reason="Denied detached action")
            act_on_shift(self.cashier.pk, shift_id=self.shift.pk, action="submit_count", counted_cash="100", expected_version=1, operation_key=uuid.uuid4(), reason="Close shift")
            self.action(draft, "cancel")
            self.assertEqual((StockBalance.objects.get().on_hand, StockBalance.objects.get().reserved), (2, 0))
            self.assertEqual((JournalEntry.objects.count(), StockMovement.objects.filter(reservation_event__isnull=False).count()), (0, 0))
            self.assertEqual(draft.events.count(), 3)

    def test_replay_conflict_stale_versions_and_revoked_role(self):
        with tenant_context(self.a):
            quote = self.quote(customer_id=self.customer.pk)
            key = uuid.uuid4()
            first = self.save(quote_id=quote.pk, operation_key=key)
            self.assertEqual(self.save(quote_id=quote.pk, operation_key=key).pk, first.pk)
            with self.assertRaises(ValidationError):
                self.save(quote_id=quote.pk, operation_key=key, reason="Different")
            action_key = uuid.uuid4()
            values = dict(order_id=first.order_id, action="confirm", expected_version=1, operation_key=action_key, reason="Synthetic confirm")
            confirmed = act_on_order(self.cashier.pk, **values)
            self.assertEqual(act_on_order(self.cashier.pk, **values).pk, confirmed.pk)
            with self.assertRaises(ValidationError):
                act_on_order(self.cashier.pk, **(values | {"operation_key": uuid.uuid4()}))
            revoke_role(self.owner.pk, assignment_id=self.catalog_grant.pk)
            self.cashier.is_superuser = True
            self.cashier.save(update_fields=["is_superuser"])
            with self.assertRaises(PermissionDenied):
                act_on_order(self.cashier.pk, **values)

    def test_repricing_requires_explicit_new_revision(self):
        with tenant_context(self.a):
            order = self.save().order
            quote_count = TaxQuote.objects.count()
            update_variant(self.owner.pk, variant_id=self.variant.pk, expected_version=1, base_price="200", active=True)
            with self.assertRaises(ValidationError):
                self.action(order)
            self.assertEqual(TaxQuote.objects.count(), quote_count)
            self.assertFalse(OrderHold.objects.exists())
            newer = self.quote(customer_id=self.customer.pk)
            self.save(order_id=order.pk, expected_version=1, quote_id=newer.pk)
            self.action(order)
            order.refresh_from_db()
            self.assertEqual((order.version, order.revisions.count()), (3, 2))
            self.assertEqual(order.revisions.get(version=1).quote.payload["sources"][0]["catalog"]["unit_price"], "100.00")

    def test_optional_image_and_prescription_version_permissions(self):
        with tenant_context(self.a):
            clinical_grant = assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="optometrist", branch_id=self.branch.pk)
            prescription = record_prescription(self.owner.pk, customer_id=self.customer.pk, branch_id=self.branch.pk, image=image_upload(), **measurements())
            order = self.save(prescription_revision_id=prescription.pk).order
            snap = order.current_revision.snapshot["prescription"]
            self.assertEqual(snap["right_sphere"], "0.00")
            self.assertTrue(snap["image"]["sha256"])
            self.assertNotIn("data", snap["image"])
            correct_prescription(self.owner.pk, prescription_id=prescription.prescription_id, expected_version=1, correction_reason="Synthetic correction", **measurements(right_sphere="1.00"))
            with self.assertRaises(ValidationError):
                self.action(order)
            order.refresh_from_db()
            self.assertEqual(order.current_revision.snapshot["prescription"], snap)
            revoke_role(self.owner.pk, assignment_id=clinical_grant.pk)
            self.assertFalse(orders_for(self.cashier.pk).exists())
            with self.assertRaises(PermissionDenied):
                self.action(order)

    def test_stock_shortage_rolls_back_all_lines_and_confirm_quote(self):
        with tenant_context(self.a):
            rows = [dict(sku=self.variant.sku, quantity=2, price_basis="gross", unit_amount="115", discount_kind="amount", discount_value="0")] * 2
            quote = self.quote(customer_id=self.customer.pk, lines=rows)
            order = self.save(quote_id=quote.pk, positions=[None, None]).order
            before = TaxQuote.objects.count()
            with self.assertRaises(ValidationError):
                self.action(order)
            self.assertEqual(TaxQuote.objects.count(), before)
            self.assertEqual(StockBalance.objects.get().reserved, 0)
            self.assertFalse(StockReservation.objects.exists())
            order.refresh_from_db()
            self.assertEqual((order.state, order.version, order.events.count()), ("draft", 1, 1))

    def test_audit_failure_rolls_back_save_confirmation_and_cancel(self):
        with tenant_context(self.a):
            with patch("sales.orders.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.save()
            self.assertFalse(SaleOrder.objects.exists())
            order = self.save().order
            with patch("sales.orders.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.action(order)
            self.assertEqual(StockBalance.objects.get().reserved, 0)
            self.action(order)
            with patch("sales.orders.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.action(order, "cancel")
            self.assertEqual(StockBalance.objects.get().reserved, 1)

    def test_concurrent_confirmations_for_last_stock_and_duplicate_key(self):
        with tenant_context(self.a):
            orders = [self.save().order for _ in range(3)]
        result = self.parallel([lambda: self.action(orders[0]), lambda: self.action(orders[1])])
        self.assertTrue(all(result))
        result = self.parallel([lambda: self.action(orders[2])] * 2)
        self.assertEqual(result, [None, None])
        with tenant_context(self.a):
            self.assertEqual(StockBalance.objects.get().reserved, 2)
            self.assertEqual(OrderHold.objects.count(), 2)

    def test_duplicate_confirmation_is_exactly_once(self):
        with tenant_context(self.a):
            order = self.save().order
        key = uuid.uuid4()
        values = dict(order_id=order.pk, action="confirm", expected_version=1, operation_key=key, reason="Synthetic duplicate")
        results = self.parallel([lambda: act_on_order(self.cashier.pk, **values)] * 2)
        self.assertIsNotNone(results[0])
        self.assertEqual(results[0], results[1])
        with tenant_context(self.a):
            self.assertEqual((OrderHold.objects.count(), StockBalance.objects.get().reserved), (1, 1))

    def test_customer_scope_branch_and_tenant_isolation(self):
        with tenant_context(self.a):
            order = self.save().order
            with self.assertRaises(ValidationError):
                self.save(order_id=order.pk, expected_version=1, shift_id=uuid.uuid4())
            CustomerBranchAccess.objects.filter(customer=self.customer).delete()
            self.assertFalse(orders_for(self.cashier.pk).exists())
            with self.assertRaises(PermissionDenied):
                self.action(order)
        with tenant_context(self.b):
            self.assertFalse(SaleOrder.objects.exists())
            with self.assertRaises(PermissionDenied):
                act_on_order(self.cashier.pk, order_id=order.pk, action="confirm", expected_version=1, operation_key=uuid.uuid4(), reason="Denied foreign order")
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            for table in ("sales_saleorder", "sales_orderrevision", "sales_orderevent", "sales_orderhold"):
                cursor.execute("SELECT to_regclass(%s)", ["public." + table])
                self.assertIsNone(cursor.fetchone()[0])

    def test_closed_shift_prevents_confirm_but_not_draft_cancellation(self):
        with tenant_context(self.a):
            order = self.save().order
            act_on_shift(self.cashier.pk, shift_id=self.shift.pk, action="submit_count", counted_cash="100", expected_version=1, operation_key=uuid.uuid4(), reason="Close shift")
            with self.assertRaises(ValidationError):
                self.action(order)
            self.action(order, "cancel")
            self.assertFalse(OrderHold.objects.exists())

    def test_postgresql_guards_and_restricted_runtime(self):
        with tenant_context(self.a):
            order = self.save().order
            with self.assertRaises(IntegrityError), transaction.atomic():
                SaleOrder.objects.filter(pk=order.pk).update(version=2)
            role = "order_test_" + uuid.uuid4().hex[:16]
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    self.action(order)
                    self.action(order, "cancel")
                for statement in ("DELETE FROM sales_saleorder WHERE false", "UPDATE sales_saleorder SET customer_id=customer_id WHERE false", "UPDATE sales_orderrevision SET snapshot=snapshot WHERE false", "DELETE FROM sales_orderevent WHERE false", "DELETE FROM sales_orderhold WHERE false"):
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_additive_migration_preserves_tax_quote(self):
        with tenant_context(self.a):
            quote = self.quote(customer_id=self.customer.pk)
            original = quote.payload
            MigrationExecutor(connection).migrate([("sales", "0004_taxquote_taxtreatmentrevision")])
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes("sales"))
            quote.refresh_from_db()
            self.assertEqual(quote.payload, original)
            self.assertFalse(SaleOrder.objects.exists())

    def test_http_customer_without_identifier_order_csrf_and_forgery(self):
        self.login("cashier")
        self.assertEqual(self.get(f"/sales/quotes/new/?customer={self.customer.pk}").status_code, 200)
        self.assertEqual(self.get("/sales/quotes/new/?customer=bad").status_code, 404)
        with tenant_context(self.a):
            quote = self.quote(customer_id=self.customer.pk)
        path = f"/sales/orders/new/{quote.pk}/"
        payload = dict(shift_id=str(self.shift.pk), reason="Synthetic HTTP", operation_key=str(uuid.uuid4()), expected_version="0", position_0="", customer_id="forged", created_by="forged")
        result = self.post(path, payload)
        self.assertEqual(result.status_code, 302)
        self.assertContains(self.get(result.url), "Synthetic order customer")
        order_id = result.url.rstrip("/").split("/")[-1]
        self.assertContains(self.get(result.url + "revisions/1/"), "115.00")
        self.assertEqual(self.get(f"/sales/quotes/new/?order={order_id}&order_version=0").status_code, 409)
        self.assertEqual(self.get(f"/sales/orders/{order_id}/review/{quote.pk}/?version=0").status_code, 409)
        self.assertEqual(self.post(result.url, dict(action="confirm", reason="Synthetic confirm", expected_version=1, operation_key=str(uuid.uuid4()))).status_code, 302)
        self.assertEqual(self.get(result.url).context["form"].fields["action"].choices, [("cancel", "إلغاء وتحرير الحجز")])
        csrf = Client(enforce_csrf_checks=True)
        csrf.cookies = self.client.cookies
        self.assertEqual(csrf.post(path, payload, HTTP_HOST="a.r05.test").status_code, 403)

    def test_tracked_lens_position_is_explicit_scoped_and_expiry_rechecked(self):
        with tenant_context(self.a):
            product = create_product(self.owner.pk, code_value="CONTACT", name="Synthetic contact", kind="contact_lens")
            variant = create_variant(self.owner.pk, product_id=product.pk, sku="CONTACT-1", unit="box", base_price="100", specifications=CONTACT)
            self.revision(variant_id=variant.pk)
            receipt = receive_stock(self.owner.pk, branch_id=self.branch.pk, variant_id=variant.pk, quantity=2, lot_code="LOT-1", expires_on=timezone.localdate()+timedelta(days=1), operation_key=uuid.uuid4(), reason="Synthetic tracking")
            position = receipt.movements.select_related("position__lot").get().position
            quote = self.quote(customer_id=self.customer.pk, lines=[dict(sku=variant.sku, quantity=1, price_basis="gross", unit_amount="115", discount_kind="amount", discount_value="0")])
            with self.assertRaises(ValidationError):
                self.save(quote_id=quote.pk)
            with self.assertRaises(ValidationError):
                self.save(quote_id=quote.pk, positions=[str(uuid.uuid4())])
            order = self.save(quote_id=quote.pk, positions=[str(position.pk)]).order
            # Synthetic passage of expiry; production does not edit lot identity.
            from inventory.models import StockLot
            StockLot.objects.filter(pk=position.lot_id).update(expires_on=timezone.localdate()-timedelta(days=1))
            with self.assertRaises(ValidationError):
                self.action(order)
            self.assertFalse(OrderHold.objects.exists())

    def test_service_has_no_stock_and_rx_requires_measurements_without_image(self):
        with tenant_context(self.a):
            product = create_product(self.owner.pk, code_value="SERVICE", name="Synthetic service", kind="service")
            variant = create_variant(self.owner.pk, product_id=product.pk, sku="SERVICE-1", unit="service", base_price="100", specifications={"description": "Synthetic adjustment"})
            self.revision(variant_id=variant.pk)
            row = dict(sku=variant.sku, quantity=1, price_basis="gross", unit_amount="115", discount_kind="amount", discount_value="0")
            order = self.save(quote_id=self.quote(customer_id=self.customer.pk, lines=[row]).pk).order
            self.action(order)
            self.assertFalse(OrderHold.objects.exists())
            product = create_product(self.owner.pk, code_value="RX", name="Synthetic RX", kind="rx_lens")
            variant = create_variant(self.owner.pk, product_id=product.pk, sku="RX-1", unit="pair", base_price="100", specifications=LENS)
            self.revision(variant_id=variant.pk)
            quote = self.quote(customer_id=self.customer.pk, lines=[row | {"sku": variant.sku}])
            with self.assertRaises(ValidationError):
                self.save(quote_id=quote.pk)
            assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="optometrist", branch_id=self.branch.pk)
            prescription = record_prescription(self.owner.pk, customer_id=self.customer.pk, branch_id=self.branch.pk, **measurements())
            order = self.save(quote_id=quote.pk, prescription_revision_id=prescription.pk).order
            self.action(order)
            self.assertIsNone(order.current_revision.snapshot["prescription"]["image"])
            self.assertFalse(OrderHold.objects.exists())

    def test_changed_customer_tax_or_member_state_prevents_confirmation(self):
        with tenant_context(self.a):
            order = self.save().order
            update_customer(self.owner.pk, customer_id=self.customer.pk, expected_version=1, first_name="Changed synthetic customer")
            with self.assertRaises(ValidationError):
                self.action(order)
            newer = self.save().order
            self.revision(expected_version=1, state="blocked", category="")
            with self.assertRaises(ValidationError):
                self.action(newer)
            set_member_active(self.owner.pk, user_id=self.cashier.pk, active=False)
            with self.assertRaises(PermissionDenied):
                self.action(newer)
            self.assertEqual(StockBalance.objects.get().reserved, 0)

    def test_preclaimed_subkeys_cannot_bypass_fresh_review_or_adopt_cancelled_stock(self):
        with tenant_context(self.a):
            order = self.save().order
            key = uuid.uuid4()
            self.quote(actor_id=self.cashier.pk, customer_id=self.customer.pk, operation_key=uuid.uuid5(key, "confirmed-quote"), reason="Synthetic action")
            update_variant(self.owner.pk, variant_id=self.variant.pk, expected_version=1, base_price="200", active=True)
            with self.assertRaises(ValidationError):
                self.action(order, operation_key=key)
            order = self.save().order
            assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="inventory_clerk", branch_id=self.branch.pk)
            key = uuid.uuid4()
            held = reserve_stock(self.cashier.pk, branch_id=self.branch.pk, variant_id=self.variant.pk, quantity=1, operation_key=uuid.uuid5(key, "hold-0"), reference="SALE-"+str(order.pk), reason="Synthetic action")
            change_reservation(self.cashier.pk, reservation_id=held.reservation_id, kind="cancel", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic prior cancellation")
            with self.assertRaises(ValidationError):
                self.action(order, operation_key=key)
            self.assertFalse(OrderHold.objects.exists())
            self.assertEqual(StockBalance.objects.get().reserved, 0)

    def test_tracking_choices_are_scoped_and_searched_before_limit(self):
        with tenant_context(self.a):
            product = create_product(self.owner.pk, code_value="DEVICE", name="Synthetic device", kind="device")
            variant = create_variant(self.owner.pk, product_id=product.pk, sku="DEVICE-CHOICE", unit="piece", base_price="100", specifications={"specification": "Synthetic device"})
            self.revision(variant_id=variant.pk)
            for serial, branch in (("UNIQUE-1", self.branch), ("UNIQUE-2", self.branch), ("HIDDEN-OTHER", self.other)):
                receive_stock(self.owner.pk, branch_id=branch.pk, variant_id=variant.pk, quantity=1, serial=serial, operation_key=uuid.uuid4(), reason="Synthetic serial")
            quote = self.quote(customer_id=self.customer.pk, lines=[dict(sku=variant.sku, quantity=1, price_basis="gross", unit_amount="115", discount_kind="amount", discount_value="0")])
        self.login("cashier")
        response = self.get(f"/sales/orders/new/{quote.pk}/?tracking_0=UNIQUE-2")
        self.assertContains(response, "UNIQUE-2")
        self.assertNotContains(response, "UNIQUE-1")
        self.assertNotContains(response, "HIDDEN-OTHER")

    def test_foreign_patient_bindings_and_sql_hold_transition_guards(self):
        with tenant_context(self.a):
            order = self.save().order
            other_customer = create_customer(self.owner.pk, branch_id=self.branch.pk, first_name="Other synthetic patient")
            other_quote = self.quote(customer_id=other_customer.pk)
            with self.assertRaises(ValidationError):
                self.save(order_id=order.pk, expected_version=1, quote_id=other_quote.pk)
            assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="optometrist", branch_id=self.branch.pk)
            other_exam = record_prescription(self.owner.pk, customer_id=other_customer.pk, branch_id=self.branch.pk, **measurements())
            with self.assertRaises(PermissionDenied):
                self.save(prescription_revision_id=other_exam.pk)
            self.action(order)
            receive_stock(self.owner.pk, branch_id=self.other.pk, variant_id=self.variant.pk, quantity=1, operation_key=uuid.uuid4(), reason="Synthetic foreign stock")
            foreign = reserve_stock(self.owner.pk, branch_id=self.other.pk, variant_id=self.variant.pk, quantity=1, operation_key=uuid.uuid4(), reason="Synthetic foreign hold")
            with self.assertRaisesMessage(IntegrityError, "order hold scope mismatch"), transaction.atomic():
                OrderHold.objects.create(revision=order.current_revision, position=2, reservation=foreign.reservation)
            with self.assertRaisesMessage(IntegrityError, "invalid order transition"), transaction.atomic():
                OrderEvent.objects.create(order=order, version=3, kind="saved", operation_key=uuid.uuid4(), payload_digest="a"*64, reason="Synthetic invalid reopen", created_by_id=self.owner.pk)
                SaleOrder.objects.filter(pk=order.pk).update(state="draft", version=3, confirmed_quote=None)
