from pathlib import Path
import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from access.models import Branch
from access.services import create_member, assign_role
from directory.provisioning import provision_company
from clinical.services import create_customer
from catalog.services import create_product, create_variant

PASSWORD = "Synthetic-Catalog-Browser-2026!"
ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CatalogBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        company = provision_company(name="شركة البصريات التجريبية", domain="localhost", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        with tenant_context(company):
            owner = get_user_model().objects.get(username="owner")
            self.branch_id = str(Branch.objects.get(code="MAIN").pk)
            customer = create_customer(owner.pk, branch_id=self.branch_id, first_name="عميل", last_name="تسعير تجريبي")
            self.customer_id = str(customer.pk)
            reader = create_member(owner.pk, username="reader", password=PASSWORD)
            assign_role(owner.pk, user_id=reader.pk, role_code="catalog_reader")
            self.stock_id = str(create_product(owner.pk, code_value="STOCK-TEST", name="عدسات مخزنية تجريبية", kind="stock_lens").pk)
            frame = create_product(owner.pk, code_value="FRAME-TEST", name="إطار تجريبي", kind="frame")
            variant = create_variant(owner.pk, product_id=frame.pk, sku="TEST-FR-52", unit="piece", base_price="99.50", specifications={"color": "Black", "eye_size": 52, "bridge": 18, "temple": 140})
            self.variant_id = str(variant.pk)
        ARTIFACTS.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def login(self, page, username="owner"):
        page.set_default_timeout(10000)
        await page.goto(self.live_server_url + "/auth/login/")
        await page.get_by_label("اسم المستخدم", exact=True).fill(username)
        await page.get_by_label("كلمة المرور", exact=True).fill(PASSWORD)
        await page.get_by_role("button", name="تسجيل الدخول", exact=True).click()
        await page.wait_for_url("**/account/")

    async def test_create_frame_variant_customer_price_refresh_and_zero_quote(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.login(page)
            await page.locator(".sidebar").get_by_role("link", name="دليل المنتجات", exact=True).click()
            await page.get_by_role("link", name="إضافة منتج", exact=True).click()
            await page.get_by_label("رمز المنتج", exact=True).fill("FRAME-NEW")
            await page.get_by_label("اسم المنتج", exact=True).fill("إطار بصريات جديد")
            await page.get_by_label("نوع المنتج", exact=True).select_option("frame")
            await page.get_by_role("button", name="حفظ", exact=True).click()
            await page.get_by_role("link", name="إضافة متغير", exact=True).click()
            await page.get_by_label("رمز المتغير SKU", exact=True).fill("FRAME-NEW-52")
            await page.get_by_label("الباركود (اختياري)", exact=True).fill("00000001234")
            await page.get_by_label("السعر الأساسي للوحدة — ريال، قبل الضريبة", exact=True).fill("150.00")
            await page.get_by_label("لون الإطار", exact=True).fill("Black")
            await page.get_by_label("عرض العدسة (ملم)", exact=True).fill("52")
            await page.get_by_label("عرض الجسر (ملم)", exact=True).fill("18")
            await page.get_by_label("طول الذراع (ملم)", exact=True).fill("140")
            await page.get_by_role("button", name="حفظ", exact=True).click()
            await expect(page.get_by_role("heading", name="FRAME-NEW-52", exact=True)).to_be_visible()
            variant_url = page.url
            await page.get_by_role("link", name="إضافة قاعدة سعر", exact=True).click()
            await page.get_by_label("الفرع", exact=True).select_option(self.branch_id)
            await page.get_by_label("سعر الوحدة — ريال، قبل الضريبة", exact=True).fill("0")
            # All fields are valid: this button must refresh choices, never create a rule.
            await page.get_by_role("button", name="تحديث خيارات العملاء", exact=True).click()
            await expect(page.get_by_role("heading", name="إضافة قاعدة سعر", exact=True)).to_be_visible()
            await page.get_by_label("العميل (اختياري)", exact=True).select_option(self.customer_id)
            await page.get_by_role("button", name="حفظ", exact=True).click()
            await page.wait_for_url(variant_url)
            self.assertEqual(await page.locator('div[aria-label="قواعد السعر"] tbody tr').count(), 1)
            await page.get_by_role("link", name="معاينة السعر", exact=True).click()
            await page.get_by_label("الفرع", exact=True).select_option(self.branch_id)
            await page.get_by_label("الكمية بوحدة البيع", exact=True).fill("3")
            await page.get_by_role("button", name="تحديث خيارات العملاء", exact=True).click()
            self.assertEqual(await page.locator("#quote-total").count(), 0)
            await page.get_by_label("العميل (اختياري)", exact=True).select_option(self.customer_id)
            await page.get_by_role("button", name="حساب السعر", exact=True).click()
            await expect(page.locator("#quote-unit-price")).to_have_text("0.00")
            await expect(page.locator("#quote-total")).to_have_text("0.00")
            await expect(page.locator("#quote-source")).to_have_text("سعر العميل")
            await page.screenshot(path=str(ARTIFACTS / "catalog-price-desktop.png"), full_page=True)
            await page.goto(variant_url)
            await page.get_by_role("button", name="إيقاف قاعدة", exact=False).click()
            await expect(page.get_by_text("موقوفة", exact=True)).to_be_visible()
            await page.goto(self.live_server_url + "/catalog/")
            await page.get_by_label("البحث في المنتجات", exact=True).fill("00000001234")
            await page.get_by_role("button", name="بحث", exact=True).click()
            await expect(page.get_by_role("link", name="عرض إطار بصريات جديد", exact=True)).to_be_visible()
            await browser.close()

    async def fill_stock(self, page, sku):
        for label, value in (("رمز المتغير SKU", sku), ("السعر الأساسي للوحدة — ريال، قبل الضريبة", "19.99"), ("مادة العدسة", "Resin"), ("معامل الانكسار", "1.60"), ("قطر العدسة (ملم)", "70"), ("SPH", "0"), ("CYL", "0"), ("الطلاءات (افصل بفاصلة)", "AR, UV")):
            await page.get_by_label(label, exact=True).fill(value)
        await page.get_by_label("وحدة البيع", exact=True).select_option("pair")
        await page.get_by_label("تصميم العدسة", exact=True).select_option("single")

    async def test_mobile_no_javascript_stock_lens_duplicate_and_price(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 390, "height": 844}, java_script_enabled=False, is_mobile=True, has_touch=True)
            await self.login(page)
            form_url = self.live_server_url + f"/catalog/products/{self.stock_id}/variants/new/"
            await page.goto(form_url)
            await self.fill_stock(page, "STOCK-PAIR-0")
            for width in (390, 768, 1440):
                await page.set_viewport_size({"width": width, "height": 900})
                self.assertEqual(await page.evaluate("innerWidth"), width)
                self.assertEqual(await page.evaluate("document.documentElement.getBoundingClientRect().x"), 0)
                self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.get_by_role("button", name="حفظ", exact=True).click()
            await expect(page.get_by_role("heading", name="STOCK-PAIR-0", exact=True)).to_be_visible()
            variant_url = page.url
            await page.evaluate("window.scrollTo(0,0)")
            await page.screenshot(path=str(ARTIFACTS / "catalog-variant-mobile.png"), full_page=True)
            await page.goto(form_url)
            await self.fill_stock(page, "DUPLICATE-PAIR")
            await page.get_by_label("الطلاءات (افصل بفاصلة)", exact=True).fill("uv, ar, AR")
            await page.get_by_role("button", name="حفظ", exact=True).click()
            await expect(page.get_by_role("alert")).to_be_visible()
            await expect(page.get_by_text("يوجد متغير بالمواصفات ووحدة البيع نفسيهما.", exact=False)).to_be_visible()
            await page.goto(variant_url)
            await page.get_by_role("link", name="معاينة السعر", exact=True).click()
            await page.get_by_label("الفرع", exact=True).select_option(self.branch_id)
            await page.get_by_label("الكمية بوحدة البيع", exact=True).fill("3")
            await page.get_by_role("button", name="حساب السعر", exact=True).click()
            await expect(page.locator("#quote-total")).to_have_text("59.97")
            await browser.close()

    async def test_catalog_reader_has_no_management_or_customer_price_data(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await self.login(page, "reader")
            await page.goto(self.live_server_url + "/catalog/")
            self.assertEqual(await page.get_by_role("link", name="إضافة منتج", exact=True).count(), 0)
            await page.goto(self.live_server_url + f"/catalog/variants/{self.variant_id}/")
            self.assertEqual(await page.get_by_role("link", name="إضافة قاعدة سعر", exact=True).count(), 0)
            self.assertEqual(await page.get_by_role("link", name="تحديث السعر والحالة", exact=True).count(), 0)
            self.assertEqual(await page.get_by_role("link", name="معاينة السعر", exact=True).count(), 0)
            response = await page.goto(self.live_server_url + f"/catalog/variants/{self.variant_id}/quote/")
            self.assertEqual(response.status, 403)
            response = await page.goto(self.live_server_url + f"/catalog/variants/{self.variant_id}/edit/")
            self.assertEqual(response.status, 403)
            await browser.close()
