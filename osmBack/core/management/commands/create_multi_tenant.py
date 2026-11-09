from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import get_tenant_model, get_tenant_domain_model, schema_context
from django.contrib.auth import get_user_model
from django.core.management import call_command
import getpass
import datetime
import json
import os
from django.conf import settings  # لإحضار TENANT_BASE_DOMAIN من settings

TENANT_BASE_DOMAIN = getattr(settings, 'TENANT_BASE_DOMAIN', 'localhost')  # fallback


class Command(BaseCommand):
    help = "Create tenants with schema, run migrations, and create superuser safely in the correct schema."

    def add_arguments(self, parser):
        parser.add_argument('--config', type=str, help='Path to JSON config file for bulk tenant creation')
        parser.add_argument('--schema', type=str, help='Schema name (e.g. tenant1)')
        parser.add_argument('--name', type=str, help='Tenant name')
        # parser.add_argument('--domain', type=str, help='Tenant domain')
        parser.add_argument('--paid_until', type=str, default='2030-12-31', help='Paid until date')
        parser.add_argument('--trial', action='store_true', help='Mark as trial tenant')
        parser.add_argument('--create_superuser', action='store_true', help='Create superuser for tenant')
        parser.add_argument('--username', type=str, help='Superuser username')
        parser.add_argument('--email', type=str, help='Superuser email')

    def handle(self, *args, **options):
        if options.get('config'):
            config_path = options['config']
            if not os.path.exists(config_path):
                raise CommandError(f"❌ Config file '{config_path}' not found.")

            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                raise CommandError(f"❌ Invalid JSON in '{config_path}'")

            for tenant_data in config_data:
                self.create_tenant_from_config(tenant_data)

        else:
            self.create_tenant_from_config(options)

            
    def create_tenant_from_config(self, config):
        name = config['name']
        schema_name = name.lower().replace(" ", "_")  # سكيمة لا تقبل فراغات
        domain_url = f"{schema_name}.{TENANT_BASE_DOMAIN}"

        tenant_model = get_tenant_model()

        if tenant_model.objects.filter(schema_name=schema_name).exists():
            self.stdout.write(self.style.WARNING(f"⚠️ Schema '{schema_name}' already exists. Skipping..."))
            return

        # إنشاء التينانت
        tenant = tenant_model(
            schema_name=schema_name,
            name=name,
            paid_until=datetime.datetime.strptime(config['paid_until'], "%Y-%m-%d").date(),
            on_trial=config.get('trial', False)
        )
        tenant.save()

        # إنشاء الدومين تلقائيًا
        domain_model = get_tenant_domain_model()
        domain = domain_model(
            domain=domain_url,
            tenant=tenant,
            is_primary=True
        )
        domain.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Tenant '{schema_name}' created with domain '{domain_url}'."))


        # تنفيذ الهجرات داخل السكيمة
        try:
            with schema_context(schema_name):
                call_command('migrate', interactive=False, verbosity=0)
                self.stdout.write(self.style.SUCCESS(f"📦 Migrations completed for schema '{schema_name}'."))
        except Exception as e:
            raise CommandError(f"❌ Failed to migrate schema '{schema_name}': {e}")

        # إنشاء superuser داخل السكيمة
        if config.get('create_superuser'):
            username = config['username']
            email = config['email']
            password = getpass.getpass(f"🔐 Enter password for superuser '{username}' in '{schema_name}': ")

            with schema_context(schema_name):
                User = get_user_model()
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Superuser '{username}' already exists in schema '{schema_name}'. Skipping creation."
                    ))
                else:
                    User.objects.create_superuser(username=username, email=email, password=password,client_id=config['client_id'])
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Superuser '{username}' created in schema '{schema_name}'."
                    ))

# python manage.py create_multi_tenant --config=data/tenants_list.json

# python manage.py shell
# from django_tenants.utils import schema_context
# from django.contrib.auth import get_user_model

# with schema_context('store1'):
#     print(get_user_model().objects.all())  # ← مستخدمي tenant1

# with schema_context('public'):
#     print(get_user_model().objects.all())  # ← مستخدمي public
