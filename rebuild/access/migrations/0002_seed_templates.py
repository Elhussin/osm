from django.db import migrations


def seed(apps, schema_editor):
    Role = apps.get_model("access", "Role")
    AccessLock = apps.get_model("access", "AccessLock")
    AccessLock.objects.using(schema_editor.connection.alias).get_or_create(pk=1)
    for code in ("owner", "company_admin", "catalog_reader", "accountant", "integration_admin", "branch_manager", "cashier", "optometrist", "inventory_clerk", "insurance_officer"):
        Role.objects.using(schema_editor.connection.alias).get_or_create(code=code)


class Migration(migrations.Migration):
    dependencies = [("access", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
