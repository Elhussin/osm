# cms/management/commands/import_pages.py
import csv
import os
from django.core.management.base import BaseCommand
from wagtail.models import Page
from wagtail.images.models import Image
from cms.models import AboutPage, GenericPage
from wagtail.blocks import StreamValue

# لو تستخدم django-tenants
from django_tenants.utils import schema_context, get_tenant_model

# class Command(BaseCommand):
#     help = "Import pages from CSV into specific schema"

#     def add_arguments(self, parser):
#         parser.add_argument('csv_file', type=str, help='Path to CSV file')
#         parser.add_argument('--schema', type=str, help='Schema/tenant to import pages into', required=True)

#     def handle(self, *args, **options):
#         csv_file = options['csv_file']
#         schema_name = options['schema']

#         if not os.path.exists(csv_file):
#             self.stdout.write(self.style.ERROR(f"CSV file not found: {csv_file}"))
#             return

#         TenantModel = get_tenant_model()
#         try:
#             tenant = TenantModel.objects.get(schema_name=schema_name)
#         except TenantModel.DoesNotExist:
#             self.stdout.write(self.style.ERROR(f"Tenant/schema not found: {schema_name}"))
#             return

#         # استخدام schema context
#         with schema_context(schema_name):
#             home_page = Page.objects.get(slug='home')  # parent page

#             with open(csv_file, newline='', encoding='utf-8') as f:
#                 reader = csv.DictReader(f)
#                 for row in reader:
#                     page_type = row.get('type', 'GenericPage')
#                     title = row.get('title', 'No Title')
#                     body = row.get('body', '')

#                     if page_type == 'AboutPage':
#                         page = AboutPage(title=title, intro=body)
#                         features_json = row.get('features')
#                         if features_json:
#                             import json
#                             features_data = json.loads(features_json)
#                             page.features = StreamValue(
#                                 page.features.stream_block, features_data, True
#                             )
#                     else:
#                         page = GenericPage(title=title, body=body)

#                     # إضافة الصور لو موجودة
#                     image_path = row.get('image_path')
#                     if image_path:
#                         try:
#                             image = Image.objects.get(file=image_path)
#                             page.main_image = image
#                         except Image.DoesNotExist:
#                             self.stdout.write(self.style.WARNING(f"Image not found: {image_path}"))

#                     home_page.add_child(instance=page)
#                     page.save_revision().publish()
#                     self.stdout.write(self.style.SUCCESS(f"Imported page: {title} into schema: {schema_name}"))

import csv
import json
from django.core.management.base import BaseCommand
from wagtail.models import Page
from cms.models import GenericPage, AboutPage, ContactPage
from wagtail.blocks import StreamValue

# إذا تستخدم django-tenants
try:
    from django_tenants.utils import schema_context
    TENANTS_ENABLED = True
except ImportError:
    TENANTS_ENABLED = False

# خريطة لتحديد الـ schema وربطه بالموديل المناسب
PAGE_MODELS = {
    "GenericPage": GenericPage,
    "AboutPage": AboutPage,
    "ContactPage": ContactPage
}

class Command(BaseCommand):
    help = "Import pages from CSV file with schema, slug check, StreamField, and auto-publish"

    def add_arguments(self, parser):
        parser.add_argument(
            "--config", type=str, help="Path to the CSV file to import pages from"
        )
        parser.add_argument(
            "--schema", type=str, help="Optional DB schema to use (multi-tenant)"
        )

    def handle(self, *args, **options):
        csv_file = options["config"]
        schema_name = options.get("schema")

        if schema_name and TENANTS_ENABLED:
            with schema_context(schema_name):
                self.import_pages(csv_file)
        else:
            self.import_pages(csv_file)

    def import_pages(self, csv_file):
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                slug = row.get("slug")
                title = row.get("title", "No Title")
                page_type = row.get("type", "GenericPage")
                body = row.get("body", "")

                # تحقق من وجود الصفحة مسبقًا
                if Page.objects.filter(slug=slug).exists():
                    self.stdout.write(self.style.WARNING(
                        f"Page with slug '{slug}' already exists. Skipping..."
                    ))
                    continue

                # الحصول على الموديل المناسب
                PageModel = PAGE_MODELS.get(page_type, GenericPage)
                page = PageModel(title=title)

                # تعيين الحقول العامة
                if hasattr(page, "body"):
                    page.body = body
                if hasattr(page, "intro"):
                    page.intro = body

                # معالجة StreamField
                if hasattr(page, "features") and row.get("features"):
                    try:
                        features_data = json.loads(row["features"])
                        page.features = StreamValue(
                            page.features.stream_block,
                            features_data,
                            True
                        )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Error parsing features for page '{title}': {e}"
                        ))

                # تعيين slug يدوي
                page.slug = slug

                # ربط الصفحة بالصفحة الأصلية (home إذا موجود)
                try:
                    parent = Page.objects.get(slug="home")
                except Page.DoesNotExist:
                    parent = Page.get_first_root_node()
                parent.add_child(instance=page)

                # نشر الصفحة
                page.save_revision().publish()

                self.stdout.write(self.style.SUCCESS(
                    f"Imported page: {title} with slug: {slug} as {page_type}"
                ))

# python manage.py import_pages "data/csv/pages1.csv" --schema "store6"



# بدون schema (قاعدة البيانات الافتراضية)
# python manage.py import_pages "data/csv/pages.csv"

# مع تحديد schema (multi-tenant)
# python manage.py import_pages --config "data/csv/pages1.csv" --schema=public
