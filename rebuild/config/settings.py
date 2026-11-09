import os
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

from .environment import required, database_config

BASE_DIR = Path(__file__).resolve().parent.parent
# This exact local file is optional; CI supplies process environment instead.
# No upward search, no legacy .env, no override of process environment.
load_dotenv(BASE_DIR / ".env", override=False)
SECRET_KEY = required("SECRET_KEY")
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("Rebuild SECRET_KEY must have at least 50 characters")
ENVIRONMENT = required("ENVIRONMENT")
if ENVIRONMENT not in {"development", "test", "production"}:
    raise ImproperlyConfigured("Invalid OSM_REBUILD_ENVIRONMENT")
DEBUG = ENVIRONMENT == "development"
ALLOWED_HOSTS = [host.strip() for host in required("ALLOWED_HOSTS").split(",") if host.strip()]
if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Wildcard ALLOWED_HOSTS is prohibited")

SHARED_APPS = ("django_tenants", "directory.apps.DirectoryConfig")
TENANT_APPS = (
    "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.sessions",
    "identity.apps.IdentityConfig",
)
INSTALLED_APPS = list(SHARED_APPS) + list(TENANT_APPS)
TENANT_MODEL = "directory.Company"
TENANT_DOMAIN_MODEL = "directory.CompanyDomain"
AUTH_USER_MODEL = "identity.User"
DATABASES = {"default": database_config()}
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "config.health.HealthMiddleware",
    "config.middleware.CompanyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
PUBLIC_SCHEMA_URLCONF = "config.public_urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "__Host-erp_session" if ENVIRONMENT == "production" else "erp_rebuild_session"
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = ENVIRONMENT == "production"
CSRF_COOKIE_SECURE = ENVIRONMENT == "production"
SECURE_SSL_REDIRECT = ENVIRONMENT == "production"
SECURE_HSTS_SECONDS = 31536000 if ENVIRONMENT == "production" else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = ENVIRONMENT == "production"
SECURE_HSTS_PRELOAD = False
X_FRAME_OPTIONS = "DENY"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
