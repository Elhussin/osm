# core/management/commands/migrate_all_tenants.py

from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
    help = 'Apply migrations to all tenants including public schema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting migrations...'))

        # Apply migrations to public schema
        self.stdout.write(self.style.WARNING('Migrating public schema...'))
        with schema_context('public'):
            call_command('migrate', interactive=False)

        # Get all tenants
        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.exclude(schema_name='public')

        # Migrate each tenant schema
        for tenant in tenants:
            self.stdout.write(self.style.WARNING(f'Migrating tenant: {tenant.schema_name}'))
            connection.set_schema(tenant.schema_name)
            call_command('migrate', interactive=False)

        self.stdout.write(self.style.SUCCESS('Migrations applied to all tenants successfully!'))


# python manage.py migrate_all_tenants
