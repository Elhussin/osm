import os
import django
import sys

# Set up Django environment
sys.path.append('/app')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "optics_tenant.settings")
django.setup()

from apps.tenants.models import Client, Domain

def create_tenant():
    try:
        # Create Public Tenant
        if not Client.objects.filter(schema_name='public').exists():
            print("Creating public tenant...")
            tenant = Client(schema_name='public', name='Public Tenant')
            tenant.save()
            print("Public tenant created.")
        else:
            tenant = Client.objects.get(schema_name='public')
            print("Public tenant already exists.")

        # Create Domain
        domain_name = 'localhost'
        if not Domain.objects.filter(domain=domain_name).exists():
            print(f"Creating {domain_name} domain for public tenant...")
            domain = Domain(domain=domain_name, tenant=tenant, is_primary=True)
            domain.save()
            print(f"{domain_name} domain created.")
        else:
            print(f"{domain_name} domain already exists.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_tenant()
