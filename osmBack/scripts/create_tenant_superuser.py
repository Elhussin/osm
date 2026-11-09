# create_tenant_superuser.py

import django
import os
import sys

# تهيئة بيئة Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "optics_tenant.settings")
django.setup()

from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model

User = get_user_model()

def create_tenant_superuser(schema_name, username, email, password):
    with schema_context(schema_name):
        if User.objects.filter(username=username).exists():
            print(f"❗ Superuser '{username}' already exists in schema '{schema_name}'.")
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"✅ Superuser '{username}' created successfully in schema '{schema_name}'.")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("❌ Usage: python create_tenant_superuser.py <schema_name> <username> <email> <password>")
        sys.exit(1)

    schema_name = sys.argv[1]
    username = sys.argv[2]
    email = sys.argv[3]
    password = sys.argv[4]

    create_tenant_superuser(schema_name, username, email, password)



# run code
# python manage.py shell
# from scripts.create_tenant_superuser import create_tenant_superuser

# create_tenant_superuser("store2", "admin", "admin@store2.com", "admin123")

# OR

#  python scripts/create_tenant_superuser.py store2 admin admin@store2.com admin1234
