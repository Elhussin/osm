"""Explicit rebuild-only configuration. Never fall back to legacy DB_* variables."""
import os
from django.core.exceptions import ImproperlyConfigured

PREFIX = "OSM_REBUILD_"


def required(name):
    value = os.environ.get(PREFIX + name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Missing {PREFIX}{name}")
    return value


def database_config():
    name = required("DB_NAME")
    if not name.startswith("optics_rebuild_"):
        raise ImproperlyConfigured("Rebuild DB_NAME must start with optics_rebuild_")
    mode = os.environ.get(PREFIX + "DB_MODE", "runtime")
    if mode not in {"runtime", "migration"}:
        raise ImproperlyConfigured("DB_MODE must be runtime or migration")
    return {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": name,
        "USER": "optics_rebuild_runtime" if mode == "runtime" else required("DB_USER"),
        "PASSWORD": required("RUNTIME_DB_PASSWORD") if mode == "runtime" else required("DB_PASSWORD"),
        "HOST": required("DB_HOST"),
        "PORT": os.environ.get(PREFIX + "DB_PORT", "55432"),
        "CONN_MAX_AGE": 0,
        "TEST": {"NAME": "test_" + name},
    }
