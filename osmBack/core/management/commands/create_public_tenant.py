from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, get_tenant_domain_model


class Command(BaseCommand):
    help = "Create the public tenant with custom data"

    def add_arguments(self, parser):
        parser.add_argument('--domain', type=str, default='localhost', help='Domain name for the public tenant')
        parser.add_argument('--name', type=str, default='Main Site', help='Name of the tenant')
        parser.add_argument('--paid_until', type=str, default='2030-12-31', help='Paid until date in YYYY-MM-DD')
        parser.add_argument('--trial', action='store_true', help='Set tenant as on trial')
        parser.add_argument('--password', type=str, help='Password for the public superuser (prompts if missing)')

    def handle(self, *args, **options):
        TenantModel = get_tenant_model()
        DomainModel = get_tenant_domain_model()

        # Parse options
        domain = options['domain']
        name = options['name']
        paid_until = options['paid_until']
        on_trial = options['trial']
        password = options['password']

        tenant, created = TenantModel.objects.get_or_create(
            schema_name='public',
            defaults={
                'name': name,
                'paid_until': paid_until,
                'on_trial': on_trial
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Public tenant created: {name}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️ Public tenant "{name}" already exists. Checking components...'))

        from django.core.management import call_command
        from apps.users.models import Role

        # 1. Migrate (always safe)
        self.stdout.write("Checking migrations...")
        call_command('migrate_all_tenants')

        # 2. Import CSV data (safe, uses get_or_create internally)
        self.stdout.write("Syncing CSV data...")
        call_command('import_csv_with_foreign', config='data/csv_config.json', schema='public')

        # 3. Ensure Owner Role exists
        self.stdout.write("Verifying roles...")
        owner_role, role_created = Role.objects.get_or_create(name='owner', defaults={'description': 'System Owner'})
        if role_created:
            self.stdout.write(self.style.SUCCESS("✅ Created 'owner' role."))
        
        # 4. Create/Verify Admin User
        self.stdout.write("Verifying admin user...")
        call_command('create_tenant_admin', 
            schema_name='public',
            username='admin',
            email='admin@public.com',
            password=password,
            role_id=str(owner_role.id),
            client_id=str(tenant.id)
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Public tenant setup complete.'))

        domain_obj, domain_created = DomainModel.objects.get_or_create(
            domain=domain,
            tenant=tenant,
            is_primary=True
        )

        if domain_created:
            self.stdout.write(self.style.SUCCESS(f'✅ Domain {domain} assigned to tenant.'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️ Domain {domain} already exists.'))
# استخدام القيم الافتراضية
# python manage.py create_public_tenant

# تمرير بيانات مخصصة
# python manage.py create_public_tenant --domain=localhost --name="Solo Vizion" --paid_until=2032-01-01 --trial
