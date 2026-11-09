import csv
import os
import sys
import django
import json
from django.apps import apps

# إعداد مسار المشروع
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "optics_tenant.settings")
django.setup()

from django_tenants.utils import schema_context


def import_csv_to_model(schema_name, app_label, model_name, csv_file_path, foreign_keys):
    print(f"\n🔄 Importing: {csv_file_path} ➜ {schema_name}.{app_label}.{model_name}")

    with schema_context(schema_name):
        try:
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except LookupError:
            print(f"❌ Model {app_label}.{model_name} not found.")
            return

        created_count = 0
        skipped_count = 0
        failed_rows = []

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            model_fields = {
                field.name: field
                for field in model._meta.get_fields()
                if field.concrete and not field.auto_created
            }

            for row_num, row in enumerate(reader, start=2):  # start=2 بسبب رأس الجدول
                data = {}
                skip_row = False

                for field_name, field in model_fields.items():
                    if field_name not in row or not row[field_name]:
                        continue

                    # التعامل مع العلاقات
                    if field.is_relation and field.many_to_one:
                        rel_model = field.related_model
                        fk_config = foreign_keys.get(field_name, {})
                        lookup_field = fk_config.get("lookup_field", "id")
                        create_if_missing = fk_config.get("create_if_missing", False)

                        try:
                            rel_obj = rel_model.objects.get(**{lookup_field: row[field_name]})
                        except rel_model.DoesNotExist:
                            if create_if_missing:
                                try:
                                    rel_obj = rel_model.objects.create(**{lookup_field: row[field_name]})
                                    print(f"🆕 Created new {rel_model.__name__}: {row[field_name]}")
                                except Exception as e:
                                    print(f"❌ Failed to create {rel_model.__name__}: {e}")
                                    failed_rows.append(row_num)
                                    skip_row = True
                                    break
                            else:
                                print(f"⚠️ Row {row_num}: FK {field_name} not found: {row[field_name]}")
                                failed_rows.append(row_num)
                                skip_row = True
                                break
                        data[field.name] = rel_obj
                    else:
                        data[field_name] = row[field_name]

                if skip_row:
                    skipped_count += 1
                    continue

                try:
                    obj, created = model.objects.get_or_create(**data)
                    if created:
                        print(f"✅ Created: {obj}")
                        created_count += 1
                    else:
                        print(f"🔁 Exists: {obj}")
                        skipped_count += 1
                except Exception as e:
                    print(f"❌ Error on row {row_num}: {e}")
                    failed_rows.append(row_num)

        print(f"\n📊 Summary for {model_name} in schema {schema_name}:")
        print(f"✅ Created: {created_count}")
        print(f"🔁 Skipped (Exists or Errors): {skipped_count}")
        if failed_rows:
            print(f"❌ Failed Rows: {failed_rows}")


def run_batch_import(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config_list = json.load(f)

    for config in config_list:
        import_csv_to_model(
            schema_name=config["schema"],
            app_label=config["app"],
            model_name=config["model"],
            csv_file_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), config["csv"]),
            foreign_keys=config.get("foreign_keys", {})
        )


if __name__ == "__main__":
    run_batch_import(os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv/csv_config.json"))

# python scripts/add_many_csv_with_forginKey.py
