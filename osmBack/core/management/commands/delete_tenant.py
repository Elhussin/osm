from django.core.management.base import BaseCommand, CommandError
from apps.tenants.models import Client  # غيّر حسب مسار موديل التينانت الخاص بك
from django.db import connection, transaction

class Command(BaseCommand):
    help = 'Delete a tenant by schema name and drop its schema from PostgreSQL.'

    # def add_arguments(self, parser):
    #     parser.add_argument('schema_name', type=str, help='The schema name of the tenant to delete')
    #     parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')
    def add_arguments(self, parser):
        parser.add_argument('--schema_name', '-s', type=str, help='The schema name of the tenant to delete')
        parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')


    def handle(self, *args, **options):
        schema_name = options['schema_name'] if 'schema_name' in options else options.get('s')

        try:
            tenant = Client.objects.get(schema_name=schema_name)
        except Client.DoesNotExist:
            raise CommandError(f'Tenant with schema name "{schema_name}" does not exist.')

        # التأكيد
        if not options['force']:
            self.stdout.write(self.style.WARNING(f'⚠️ Are you sure you want to delete tenant "{schema_name}" and drop its schema? [y/N]'))
            confirm = input()
            if confirm.lower() != 'y':
                self.stdout.write(self.style.NOTICE('❌ Aborted by user.'))
                return

        try:
            # حذف سجل التينانت من قاعدة البيانات
            tenant.delete()
            self.stdout.write(self.style.SUCCESS(f'✔️ Tenant "{schema_name}" deleted from database.'))

            # حذف السكيمة من PostgreSQL
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')
            self.stdout.write(self.style.SUCCESS(f'✔️ Schema "{schema_name}" dropped from PostgreSQL.'))

        except Exception as e:
            raise CommandError(f'Error while deleting tenant or dropping schema: {e}')


# python manage.py delete_tenant -s store1 --force
