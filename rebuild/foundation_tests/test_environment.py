import os
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from config.environment import database_config, required


class ConfigurationTests(SimpleTestCase):
    def test_legacy_database_variables_cannot_supply_settings(self):
        with patch.dict(os.environ, {"DB_NAME": "legacy", "DB_PASSWORD": "not-a-real-secret"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                database_config()

    def test_legacy_database_name_is_rejected(self):
        with patch.dict(os.environ, {"OSM_REBUILD_DB_NAME": "optics_tenant"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                database_config()

    def test_missing_secret_is_explicit(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesMessage(ImproperlyConfigured, "Missing OSM_REBUILD_SECRET_KEY"):
                required("SECRET_KEY")

    def test_test_database_name_is_distinct_and_prefixed(self):
        values = {"DB_NAME": "optics_rebuild_ci", "DB_USER": "test", "DB_PASSWORD": "synthetic", "DB_HOST": "localhost", "DB_MODE": "migration"}
        with patch.dict(os.environ, {"OSM_REBUILD_" + key: value for key, value in values.items()}, clear=True):
            config = database_config()
        self.assertEqual(config["TEST"]["NAME"], "test_optics_rebuild_ci")
        self.assertEqual(config["ENGINE"], "django_tenants.postgresql_backend")

    def test_runtime_is_default_and_does_not_use_owner_credentials(self):
        values = {"DB_NAME": "optics_rebuild_ci", "DB_USER": "owner", "DB_PASSWORD": "owner-synthetic", "RUNTIME_DB_PASSWORD": "runtime-synthetic", "DB_HOST": "localhost"}
        with patch.dict(os.environ, {"OSM_REBUILD_" + key: value for key, value in values.items()}, clear=True):
            config = database_config()
        self.assertEqual(config["USER"], "optics_rebuild_runtime")
        self.assertEqual(config["PASSWORD"], "runtime-synthetic")
