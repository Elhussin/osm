import getpass
from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from apps.tenants.models import Client 
from apps.users.models import Role, User  

class Command(BaseCommand):
    help = 'Create an admin user for a specific tenant schema'

    def add_arguments(self, parser):
        parser.add_argument('--schema_name', '-s', type=str, required=True, help='Tenant schema name')
        parser.add_argument('--username', type=str, required=True, help='Username for the superuser')
        parser.add_argument('--email', type=str, required=True, help='Email for the superuser')
        parser.add_argument('--password', type=str, help='Password for the superuser ')
        parser.add_argument('--role_id', type=str, required=True, help='Role for the superuser')
        parser.add_argument('--client_id', type=str, required=True, help='Client ID for the superuser')


    def handle(self, *args, **options):
        schema_name = options['schema_name']
        username = options['username']
        email = options['email']
        password = options.get('password')
        role_id = options.get('role_id')
        client_id = options.get('client_id')
        
        if not role_id or role_id.strip() == "":
            raise CommandError("Role ID is required. Please provide a valid role ID.")

        if not client_id or client_id.strip() == "":
            raise CommandError("Client ID is required. Please provide a valid client ID.")

        if not password:
            password = getpass.getpass('Password: ')
            password2 = getpass.getpass('Confirm Password: ')
            if password != password2:
                raise CommandError("Passwords do not match.")

        try:
            with schema_context(schema_name):
                User = get_user_model()
                


                # User.objects.create_superuser(username=username, email=email, password=password, client_id=client.id, role=role.id)
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'client_id': client_id,
                        'role_id': role_id,
                        'is_superuser': True,
                        'is_staff': True
                    }
                )
                if created:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Superuser '{username}' created successfully in schema '{schema_name}'."
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Superuser '{username}' already exists in schema '{schema_name}'. Skipping creation."
                    ))

        except Exception as e:
            raise CommandError(f"Failed to create superuser: {e}")
# python manage.py create_tenant_admin --schema_name store4 --username store1 --email store4@mail.com --role_id <ID> --client_id <ID>
