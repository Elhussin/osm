import csv
import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = 'Batch import CSV files with support for ForeignKeys in tenant schemas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--config',
            type=str,
            required=True,
            help='Path to JSON config file specifying models and CSV files',
        )
        parser.add_argument(
            '--schema',
            type=str,
            required=False,
            help='Optional schema_name argument for custom use',
        )
    

    def handle(self, *args, **options):
        config_path = options['config'] 
        schema_name = options.get('schema')
        print(f"Using config file: {config_path}")
        print (f"Schema name: {schema_name}")


        if not os.path.exists(os.path.abspath(config_path)):

            raise CommandError(f"Config file does not exist: {config_path}")

        with open(os.path.abspath(config_path), 'r', encoding='utf-8') as f:
            config_list = json.load(f)


        for config in config_list:
            if schema_name:
                config["schema"] = schema_name
            schema_name =  config["schema"]
            app_label = config["app"]
            model_name = config["model"]
            csv_file_path = os.path.join(os.path.dirname(config_path), config["csv"])
            foreign_keys = config.get("foreign_keys", {})

            self.import_csv_to_model(schema_name, app_label, model_name, csv_file_path, foreign_keys)

    def import_csv_to_model(self, schema_name, app_label, model_name, csv_file_path, foreign_keys):
        self.stdout.write(f"\n🔄 Importing: {csv_file_path} ➜ {schema_name}.{app_label}.{model_name}")

        with schema_context(schema_name):
            try:
                model = apps.get_model(app_label=app_label, model_name=model_name)
            except LookupError:
                self.stderr.write(f"❌ Model {app_label}.{model_name} not found.")
                return

            created_count = 0
            skipped_count = 0
            failed_rows = []
            print(csv_file_path)
            print(os.path.abspath(csv_file_path))
            with open(os.path.abspath(csv_file_path), newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                model_fields = {
                    field.name: field
                    for field in model._meta.get_fields()
                    if field.concrete and not field.auto_created
                }

                for row_num, row in enumerate(reader, start=2):
                    data = {}
                    skip_row = False

                    for field_name, field in model_fields.items():
                        if field_name not in row or not row[field_name]:
                            continue

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
                                        self.stdout.write(f"🆕 Created new {rel_model.__name__}: {row[field_name]}")
                                    except Exception as e:
                                        self.stderr.write(f"❌ Failed to create {rel_model.__name__}: {e}")
                                        failed_rows.append(row_num)
                                        skip_row = True
                                        break
                                else:
                                    self.stderr.write(f"⚠️ Row {row_num}: FK {field_name} not found: {row[field_name]}")
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
                            self.stdout.write(f"✅ Created: {obj}")
                            created_count += 1
                        else:
                            self.stdout.write(f"🔁 Exists: {obj}")
                            skipped_count += 1
                    except Exception as e:
                        self.stderr.write(f"❌ Error on row {row_num}: {e}")
                        failed_rows.append(row_num)

            self.stdout.write(f"\n📊 Summary for {model_name} in schema {schema_name}:")
            self.stdout.write(f"✅ Created: {created_count}")
            self.stdout.write(f"🔁 Skipped (Exists or Errors): {skipped_count}")
            if failed_rows:
                self.stderr.write(f"❌ Failed Rows: {failed_rows}")


# 
# python manage.py import_csv_with_foreign --config data/csv_configo0.json --schema store1