from django.core.management import call_command
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.tenants.models import Client  # نموذج المستأجر الخاص بك

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.tenants.models import Client

class Command(BaseCommand):
    help = 'Migrate Wagtail apps to tenant schemas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schema',
            type=str,
            help='Specify a tenant schema to migrate (optional). If not provided, migrates all tenants.'
        )

    def handle(self, *args, **options):
        SHARED_APPS = (
            'django_tenants',
            'users',
            'core',
            'tenants',
            'admin_interface',
            'colorfield',
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.sites',
            'rest_framework',
            'rest_framework_simplejwt',
            'rest_framework.authtoken',
            'dj_rest_auth',
            'dj_rest_auth.registration',
            'simple_history',
            'corsheaders',
            'djmoney',
            'drf_spectacular',
            'drf_spectacular_sidecar',
            'django_extensions',
            # Wagtail CMS
            'modelcluster',
            'taggit',
            'wagtail.contrib.forms',
            'wagtail.contrib.redirects',
            'wagtail.embeds',
            'wagtail.sites',
            'wagtail.users',
            'wagtail.snippets',
            'wagtail.documents',
            'wagtail.images',
            'wagtail.search',
            'wagtail.admin',
            'wagtail',
            'wagtail.api.v2',
            'wagtail_localize',
            'cms',  # app for wagtail

        )

        # ===============================
        # TENANT_APPS
        # ===============================
        TENANT_APPS = (
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.sites',
            'django_extensions',
            'core',
            'users',
            'prescriptions',
            'products',
            'crm',
            'hrm',
            'branches',
            'accounting',
            'sales',
            # app for wagtail
            'modelcluster',
            'taggit',
            'wagtail.contrib.forms',
            'wagtail.contrib.redirects',
            'wagtail.embeds',
            'wagtail.sites',
            'wagtail.users',
            'wagtail.snippets',
            'wagtail.documents',
            'wagtail.images',
            'wagtail.search',
            'wagtail.admin',
            'wagtail',
            'wagtail.api.v2',
            'wagtail_localize',

            'cms',  # app for wagtail
        )

        AUTH_USER_MODEL = 'users.User'

        # ===============================
        # merge apps
        # ===============================
        INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

        schema_name = options.get('schema')
        success = True

        if schema_name:
            try:
                tenant = Client.objects.get(schema_name=schema_name)
                self.stdout.write(f"Migrating Wagtail apps for tenant: {tenant.schema_name}")
                with schema_context(tenant.schema_name):
                    for app in INSTALLED_APPS:
                        self.stdout.write(f"Applying migrations for {app} in schema {tenant.schema_name}")
                        try:
                            call_command('migrate', app)
                        except Exception as e:
                            self.stderr.write(f"Error migrating {app} for {tenant.schema_name}: {str(e)}")
                            success = False
                if success:
                    self.stdout.write(self.style.SUCCESS(f"Successfully migrated Wagtail apps for {tenant.schema_name}"))
                else:
                    self.stderr.write(self.style.ERROR(f"Failed to migrate some apps for {tenant.schema_name}"))
            except Client.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Tenant with schema {schema_name} does not exist"))
        else:
            tenants = Client.objects.all()
            for tenant in tenants:
                success = True
                self.stdout.write(f"Migrating Wagtail apps for tenant: {tenant.schema_name}")
                with schema_context(tenant.schema_name):
                    for app in wagtail_apps:
                        self.stdout.write(f"Applying migrations for {app} in schema {tenant.schema_name}")
                        try:
                            call_command('migrate', app)
                        except Exception as e:
                            self.stderr.write(f"Error migrating {app} for {tenant.schema_name}: {str(e)}")
                            success = False
                if success:
                    self.stdout.write(self.style.SUCCESS(f"Successfully migrated Wagtail apps for {tenant.schema_name}"))
                else:
                    self.stderr.write(self.style.ERROR(f"Failed to migrate some apps for {tenant.schema_name}"))


        # migrate_wagtail_apps

        # python manage.py migrate_wagtail_apps --schema=store6
