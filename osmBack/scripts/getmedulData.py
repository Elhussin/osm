import csv
import os
import sys
import django
from importlib import import_module
from django.apps import apps

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# إعداد بيئة Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "optics_tenant.settings")
django.setup()

# إذا كنت تستخدم django-tenants
from django_tenants.utils import schema_context

def get_data(schema_name, app_label, model_name):
    with schema_context(schema_name):
        try:
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except LookupError:
            print(f"Model {app_label}.{model_name} not found.")
            return

        data = list(model.objects.all())
        return data

def save_data_to_csv(data, csv_file_path):
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data[0].__dict__.keys())
        for item in data:
            writer.writerow(item.__dict__.values())

if __name__ == "__main__":
    schema_name = "store1"
    app_label="products"
    model_name="Attributes"   
    data = get_data(schema_name, app_label, model_name)
    print(data)
    save_data_to_csv(data, "scripts/csv/Attributes_data.csv")



#  py scripts/getmedulData.py
