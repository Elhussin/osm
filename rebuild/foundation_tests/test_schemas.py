from django.contrib.auth import authenticate, get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django_tenants.utils import schema_context
from directory.models import Company, CompanyDomain


@override_settings(ALLOWED_HOSTS=["a.example.test", "b.example.test", "unknown.example.test"], SECURE_SSL_REDIRECT=False)
class SchemaFoundationTests(TransactionTestCase):
    """I01 and foundation parts of I02/I04/I06; only uses Django's new test DB."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not connection.settings_dict["NAME"].startswith("test_optics_rebuild_"):
            raise RuntimeError("Schema tests require the isolated rebuild test database")
        connection.set_schema_to_public()
        for schema in ("foundation_a", "foundation_b"):
            company = Company.objects.create(name=schema, schema_name=schema)
            company.create_schema(check_if_exists=True, verbosity=0)
            company.state = Company.State.READY
            company.save(update_fields=["state"])
            CompanyDomain.objects.create(tenant=company, domain="a.example.test" if schema.endswith("a") else "b.example.test", is_primary=True)
        with schema_context("foundation_a"):
            cls.user_a = get_user_model().objects.create_user(username="same-login", password="Synthetic-A-password-2026")
        with schema_context("foundation_b"):
            cls.user_b = get_user_model().objects.create_user(username="same-login", password="Synthetic-B-password-2026")

    @classmethod
    def tearDownClass(cls):
        # No schema deletion command; Django destroys the isolated test DB afterward.
        connection.set_schema_to_public()
        super().tearDownClass()

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def _tables(self, schema):
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = %s", [schema])
            return {row[0] for row in cursor.fetchall()}

    def test_foundation_contract(self):
        # Keep one fixture lifecycle: TransactionTestCase flushes public tables
        # after each test, while tenant tables intentionally remain separate.
        for check in (
            self._assert_auth_and_sessions_exist_only_in_tenants,
            self._assert_same_login_has_independent_passwords,
            self._assert_session_data_is_not_shared,
            self._assert_unregistered_host_has_no_tenant_fallback,
            self._assert_context_is_restored_after_exception,
            self._assert_unready_company_is_not_routed,
        ):
            with self.subTest(check=check.__name__):
                check()

    def _assert_auth_and_sessions_exist_only_in_tenants(self):
        public = self._tables("public")
        self.assertIn("directory_company", public)
        self.assertNotIn("identity_user", public)
        self.assertNotIn("auth_group", public)
        self.assertNotIn("django_session", public)
        for schema in ("foundation_a", "foundation_b"):
            tables = self._tables(schema)
            self.assertTrue({"identity_user", "auth_group", "django_session"} <= tables)
            self.assertNotIn("directory_company", tables)

    def _assert_same_login_has_independent_passwords(self):
        with schema_context("foundation_a"):
            self.assertIsNotNone(authenticate(username="same-login", password="Synthetic-A-password-2026"))
            self.assertIsNone(authenticate(username="same-login", password="Synthetic-B-password-2026"))
        with schema_context("foundation_b"):
            self.assertIsNotNone(authenticate(username="same-login", password="Synthetic-B-password-2026"))
            self.assertIsNone(authenticate(username="same-login", password="Synthetic-A-password-2026"))

    def _assert_session_data_is_not_shared(self):
        with schema_context("foundation_a"):
            session = SessionStore()
            session["company_marker"] = "synthetic-a"
            session.save()
            key = session.session_key
        with schema_context("foundation_b"):
            self.assertIsNone(SessionStore(session_key=key).get("company_marker"))

    def _assert_unregistered_host_has_no_tenant_fallback(self):
        response = self.client.get("/not-a-probe/", HTTP_HOST="unknown.example.test")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(connection.schema_name, "public")

    def _assert_context_is_restored_after_exception(self):
        with self.assertRaises(ValueError):
            with schema_context("foundation_a"):
                raise ValueError("synthetic failure")
        self.assertEqual(connection.schema_name, "public")
        with schema_context("foundation_b"):
            self.assertEqual(get_user_model().objects.get(username="same-login").id, self.user_b.id)

    def _assert_unready_company_is_not_routed(self):
        Company.objects.filter(schema_name="foundation_a").update(state=Company.State.SUSPENDED)
        try:
            response = self.client.get("/not-a-probe/", HTTP_HOST="a.example.test")
            self.assertEqual(response.status_code, 404)
        finally:
            Company.objects.filter(schema_name="foundation_a").update(state=Company.State.READY)
