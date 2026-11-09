# core/management/commands/create_tenant_and_migrate.py

from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from django.core.management import call_command
from django.conf import settings
from django.utils.text import slugify

from apps.tenants.models import Client, Domain  # عدّل حسب مسار Tenant model في مشروعك

class Command(BaseCommand):
    help = 'Create a new tenant and apply migrations.'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Tenant name (e.g., My Store)')
        parser.add_argument('schema_name', type=str, help='Schema name (e.g., store1)')
        # parser.add_argument('--domain', type=str, help='Domain/Subdomain (e.g., store1.example.com)', required=False)

    def handle(self, *args, **options):
        name = options['name']
        schema_name = slugify(options['schema_name'])
        domain_url = f'{schema_name}.{settings.TENANT_BASE_DOMAIN}'

        self.stdout.write(self.style.NOTICE(f'Creating tenant: {name} | schema: {schema_name}'))

        # Step 1: Create the tenant
        tenant = Client(
            name=name,
            schema_name=schema_name,
            paid_until='2030-01-01',
            on_trial=True
        )
        tenant.save()
        print(tenant)
        self.stdout.write(self.style.SUCCESS('Tenant created successfully.'))

        # Step 2: Create the domain/subdomain
        domain = Domain()
        domain.domain = domain_url
        domain.tenant = tenant
        domain.is_primary = True
        domain.save()
        self.stdout.write(self.style.SUCCESS(f'Domain "{domain.domain}" created and assigned to tenant.'))

        # call_command('migrate', schema_name=schema_name)
        # Step 3: Run migrations on the new schema
        self.stdout.write(self.style.WARNING('Applying migrations to new tenant...'))
        with schema_context(schema_name):

            call_command('import_csv_with_foreign', schema=schema_name, config="data/csv_config.json")
            call_command('import_pages', schema=schema_name, config="data/csv/pages1.csv")
            call_command('create_tenant_superuser', schema_name=schema_name, username='admin', email='admin@public.com')

        self.stdout.write(self.style.SUCCESS(f'Tenant "{name}" created and migrated successfully!'))

# python manage.py create_tenant_and_migrate "My Store" store1
