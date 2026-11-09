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

SHARED_APPS = ("django_tenants", "directory.apps.DirectoryConfig", "django.contrib.staticfiles")
TENANT_APPS = (
    "django.contrib.contenttypes", "django.contrib.auth", "django.contrib.sessions",
    "identity.apps.IdentityConfig",
    "access.apps.AccessConfig",
    "django.contrib.messages", "workspace.apps.WorkspaceConfig",
    "clinical.apps.ClinicalConfig",
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
    "django.contrib.messages.middleware.MessageMiddleware",
    "identity.middleware.BoundSessionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.template.context_processors.csrf", "django.contrib.messages.context_processors.messages", "workspace.context.ui_context"]}}]
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
FILE_UPLOAD_HANDLERS = ["clinical.images.BoundedUploadHandler", "django.core.files.uploadhandler.MemoryFileUploadHandler", "django.core.files.uploadhandler.TemporaryFileUploadHandler"]
FILE_UPLOAD_MAX_MEMORY_SIZE = 512 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 1
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
INVITE_DELIVERY = os.environ.get("OSM_REBUILD_INVITE_DELIVERY", "manual")
if INVITE_DELIVERY not in {"manual", "smtp"}:
    raise ImproperlyConfigured("INVITE_DELIVERY must be manual or smtp")
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("OSM_REBUILD_SMTP_HOST", "")
EMAIL_PORT = int(os.environ.get("OSM_REBUILD_SMTP_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("OSM_REBUILD_SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("OSM_REBUILD_SMTP_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("OSM_REBUILD_SMTP_TLS", "true").lower() == "true"
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get("OSM_REBUILD_SMTP_FROM", "")
if INVITE_DELIVERY == "smtp" and (not EMAIL_HOST or not DEFAULT_FROM_EMAIL):
    raise ImproperlyConfigured("SMTP delivery requires explicit host and from address")
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
