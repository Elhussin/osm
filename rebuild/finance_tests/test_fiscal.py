from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
import uuid
from psycopg import sql
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.test import Client, SimpleTestCase, TransactionTestCase, override_settings
from django_tenants.utils import tenant_context
from access.models import AuditEvent, RoleAssignment
from access.services import assign_role, create_member, revoke_role
from directory.db_roles import grant_tenant_runtime
from finance.models import FiscalProfileRevision
from finance.readiness import readiness
from finance.services import PROFILE_FIELDS, latest_profile, profile_values, save_fiscal_profile
from workspace_tests import test_workspace as fixtures


def data(**changes):
    # Synthetic data only. A structurally valid VAT identifier is not verified.
    values = dict.fromkeys(PROFILE_FIELDS, "")
    values.update(legal_name="Synthetic fiscal seller", registration_status="registered", vat_number="300000000000003",
        commercial_registration="SYNTHETIC-CR", street="Synthetic street", building_number="1234", additional_number="5678",
        district="Synthetic district", city="Synthetic city", postal_code="12345")
    return values | changes


class FiscalValidationTests(SimpleTestCase):
    def test_identifiers_and_registration_are_explicit_and_no_connection_fields(self):
        for change in ({"vat_number": "3" * 14}, {"vat_number": "٣" * 15}, {"vat_number": "３" * 15},
                       {"registration_status": "not_registered"}, {"registration_status": "unknown"},
                       {"building_number": "-123"}, {"postal_code": "1234"}, {"additional_number": "abcd"}, {"legal_name": 5}):
            with self.subTest(change=change), self.assertRaises(ValidationError):
                profile_values(data(**change))
        with self.assertRaises(ValidationError):
            profile_values(data() | {"connected": True})
        self.assertEqual(profile_values(data(registration_status="not_registered", vat_number=""))["vat_number"], "")
        empty = readiness(None)
        self.assertFalse(empty.seller_data_complete)
        self.assertFalse(empty.can_issue_tax_invoice or empty.can_submit_to_zatca or empty.registration_verified)


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FiscalProfileTests(TransactionTestCase):
    setUp = fixtures.WorkspaceTests.setUp
    login = fixtures.WorkspaceTests.login
    get = fixtures.WorkspaceTests.get
    post = fixtures.WorkspaceTests.post

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def save(self, **changes):
        values = dict(data=data(), expected_version=0, operation_key=uuid.uuid4(), reason="Synthetic setup")
        values.update(changes)
        return save_fiscal_profile(self.owner.pk, **values)

    def test_revisions_preserve_original_and_complete_data_never_enables_invoicing(self):
        with tenant_context(self.a):
            first = self.save()
            check = readiness(first)
            self.assertTrue(check.seller_data_complete)
            self.assertFalse(check.registration_verified or check.can_issue_tax_invoice or check.can_submit_to_zatca)
            second = self.save(data=data(city="New synthetic city"), expected_version=1, reason="Synthetic correction")
            first.refresh_from_db()
            self.assertEqual(first.city, "Synthetic city")
            self.assertEqual((first.version, second.version, latest_profile().pk), (1, 2, second.pk))
            draft = self.save(data=data(registration_status="unknown", vat_number="", street=""), expected_version=2)
            self.assertFalse(readiness(draft).seller_data_complete)
            self.assertIn("الشارع", readiness(draft).missing_fields)
            self.assertEqual(AuditEvent.objects.filter(action="finance.profile_saved").count(), 3)

    def test_replay_reauthorizes_and_changed_payload_or_stale_version_rejected(self):
        with tenant_context(self.a):
            key = uuid.uuid4()
            first = self.save(operation_key=key)
            self.assertEqual(self.save(operation_key=key).pk, first.pk)
            with self.assertRaises(ValidationError):
                self.save(operation_key=key, data=data(city="Changed"))
            with self.assertRaises(ValidationError):
                self.save(expected_version=0)
            admin = create_member(self.owner.pk, username="companyadmin", password=fixtures.PASSWORD)
            grant = assign_role(self.owner.pk, user_id=admin.pk, role_code="company_admin")
            kwargs = dict(data=data(), expected_version=1, operation_key=uuid.uuid4(), reason="Admin setup")
            save_fiscal_profile(admin.pk, **kwargs)
            revoke_role(self.owner.pk, assignment_id=grant.pk)
            admin.is_superuser = True
            admin.save(update_fields=["is_superuser"])
            with self.assertRaises(PermissionDenied):
                save_fiscal_profile(admin.pk, **kwargs)

    def test_permission_and_tenant_scope_and_no_public_profile(self):
        with tenant_context(self.a):
            self.save()
            integration = create_member(self.owner.pk, username="integrator", password=fixtures.PASSWORD)
            assign_role(self.owner.pk, user_id=integration.pk, role_code="integration_admin")
            for actor in (self.cashier, integration):
                with self.assertRaises(PermissionDenied):
                    save_fiscal_profile(actor.pk, data=data(), expected_version=1, operation_key=uuid.uuid4(), reason="Denied")
        self.login("cashier")
        self.assertEqual(self.get("/account/fiscal/").status_code, 403)
        self.assertEqual(self.post("/account/fiscal/", {}).status_code, 403)
        foreign = Client()
        self.assertEqual(foreign.post("/auth/login/", {"username": "owner", "password": fixtures.PASSWORD}, HTTP_HOST="b.r05.test").status_code, 302)
        response = foreign.get("/account/fiscal/", HTTP_HOST="b.r05.test")
        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertNotContains(response, "Synthetic fiscal seller")
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('public.finance_fiscalprofilerevision')")
            self.assertIsNone(cursor.fetchone()[0])
        with tenant_context(self.b):
            self.assertFalse(FiscalProfileRevision.objects.exists())

    def test_http_drafts_history_csrf_and_forged_connection_state(self):
        initial = self.get("/account/fiscal/")
        form = initial.context["form"]
        values = data() | {"reason": "Browser setup", "expected_version": 0, "operation_key": str(form.initial["operation_key"]),
            "connected": "true", "compliant": "true", "environment": "production", "can_submit_to_zatca": "true"}
        self.assertEqual(self.post("/account/fiscal/", values).status_code, 302)
        response = self.get("/account/fiscal/")
        self.assertContains(response, "الربط مع هيئة الزكاة والضريبة والجمارك غير مفعل")
        self.assertFalse(response.context["readiness"].can_submit_to_zatca)
        bad = values | {"operation_key": str(uuid.uuid4()), "expected_version": 1, "vat_number": "123"}
        self.assertEqual(self.post("/account/fiscal/", bad).status_code, 422)
        stale = values | {"operation_key": str(uuid.uuid4())}
        self.assertEqual(self.post("/account/fiscal/", stale).status_code, 422)
        strict = Client(enforce_csrf_checks=True)
        strict.cookies = self.client.cookies
        self.assertEqual(strict.post("/account/fiscal/", values, HTTP_HOST="a.r05.test").status_code, 403)
        with tenant_context(self.a):
            self.assertEqual(FiscalProfileRevision.objects.count(), 1)

    def test_failure_rolls_back_entire_revision_and_audit(self):
        with tenant_context(self.a):
            with patch("finance.services.audit", side_effect=RuntimeError("Synthetic failure")), self.assertRaises(RuntimeError):
                self.save()
            self.assertFalse(FiscalProfileRevision.objects.exists())
            self.assertFalse(AuditEvent.objects.filter(action="finance.profile_saved").exists())

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

    def test_concurrent_same_key_and_conflicting_versions(self):
        key = uuid.uuid4()
        results = self.parallel([lambda: self.save(operation_key=key)] * 2)
        self.assertIsNotNone(results[0])
        self.assertEqual(results[0], results[1])
        results = self.parallel([lambda: self.save(expected_version=1, data=data(city="A")), lambda: self.save(expected_version=1, data=data(city="B"))])
        self.assertEqual(sum(value is not None for value in results), 1)
        with tenant_context(self.a):
            self.assertEqual(FiscalProfileRevision.objects.count(), 2)
            self.assertEqual(latest_profile().version, 2)

    def test_postgres_constraints_and_limited_runtime_preserve_history(self):
        role = "r09_fiscal_" + uuid.uuid4().hex
        with tenant_context(self.a):
            first = self.save()
            for fields in ({"version": 0}, {"currency": "USD"}, {"country_code": "XX"}, {"vat_number": "x"},
                           {"registration_status": "not_registered"}, {"version": 1}, {"operation_key": first.operation_key}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    values = {field.name: getattr(first, field.name) for field in first._meta.fields if field.name not in {"id", "created_at"}}
                    values.update(version=2, operation_key=uuid.uuid4())
                    values.update(fields)
                    FiscalProfileRevision.objects.create(**values)
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
                cursor.execute(sql.SQL("GRANT SELECT ON public.directory_company TO {}").format(sql.Identifier(role)))
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                    self.save(expected_version=1, data=data(city="Runtime city"))
                for statement in ("UPDATE finance_fiscalprofilerevision SET legal_name=legal_name WHERE false", "DELETE FROM finance_fiscalprofilerevision WHERE false"):
                    with self.assertRaises(ProgrammingError), transaction.atomic(), connection.cursor() as cursor:
                        cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                        cursor.execute(statement)
                self.assertEqual(FiscalProfileRevision.objects.count(), 2)
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
