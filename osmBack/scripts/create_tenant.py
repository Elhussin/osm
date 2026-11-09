# -*- coding: utf-8 -*-
# create_tenant_superuser.py

import django
import os
import sys

# تهيئة بيئة Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "optics_tenant.settings")
django.setup()

from django_tenants.utils import schema_context
from django.contrib.auth import get_user_model
from apps.tenants.models import Client, Domain
import datetime

def create_tenant_with_admin(schema_name, name, admin_email, admin_username, admin_password):
    # إنشاء العميل
    tenant = Client(
        schema_name=schema_name,
        name=name,
        paid_until=datetime.date(2030, 1, 1),
        on_trial=False
    )
    tenant.save()

    # ربط الدومين
    domain = Domain()
    domain.domain = schema_name + ".localhost"  # مثال: store2.localhost
    domain.tenant = tenant
    domain.is_primary = True
    domain.save()

    # إنشاء مستخدم admin داخل السكيما الخاصة بالعميل
    with schema_context(schema_name):
        User = get_user_model()
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )
            print(f"[✓] Created tenant '{schema_name}' with superuser '{admin_username}'")
        else:
            print("[!] User already exists")

# مثال على الاستخدام المباشر عند تشغيل الملف كـ script
if __name__ == "__main__":
    print("🔧 Creating tenant with superuser...")
    if len(sys.argv) != 6:
        print("❌ Usage: python create_tenant_superuser.py <schema_name> <name> <admin_email> <admin_username> <admin_password>")
        sys.exit(1)
    print("✅ Creating tenant...")
    print(sys.argv)
    schema_name = sys.argv[1]
    name = sys.argv[2]
    admin_email = sys.argv[3]
    admin_username = sys.argv[4]
    admin_password = sys.argv[5]

    create_tenant_with_admin(schema_name, name, admin_email, admin_username, admin_password)


# run code
# python scripts/create_tenant.py store1 "Solo Vision 5" admin@store5.com admin admin123


# python manage.py shell
# from scripts.create_tenant import create_tenant_with_admin

# create_tenant_with_admin(
#     schema_name="store2",
#     name="Solo Vision 5",

#     admin_email="admin@store3.com",
#     admin_username="admin",
#     admin_password="admin123"
# )
