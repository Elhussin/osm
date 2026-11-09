import os
import django
from django.core.management import call_command

# إعداد البيئة
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "optics_tenant.settings")  # عدّل اسم مشروعك
django.setup()

# تنفيذ الأوامر
# call_command("create_multi_tenant", config="data/tenants_list.json")
call_command("create_public_tenant", domain="localhost", name="Solo Vizion", paid_until="2032-01-01", trial=True)
call_command("import_csv_with_foreign", config="data/csv_config.json")
call_command("create_tenant_superuser", schema_name="public", username="admin", email="admin@public.com", roler_id="2" )
# call_command("import_csv_with_foreign", config="data/csv_config.json")


# python scripts/run_commands.py
# 1013639602