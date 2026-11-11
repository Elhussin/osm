import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from catalog.services import create_product, create_variant
from catalog_tests.test_catalog import FRAME
from finance.services import save_fiscal_profile
from finance_tests.test_fiscal import data
from sales.taxes import revise_treatment
from . import test_workspace_browser as fixtures


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class RetailTaxBrowserTests(StaticLiveServerTestCase):
    sign_in = fixtures.WorkspaceBrowserTests.sign_in

    def setUp(self):
        fixtures.WorkspaceBrowserTests.setUp(self)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            product = create_product(owner.pk, code_value="BROWSER-TAX", name="إطار اختبار الضريبة", kind="frame")
            self.variant = create_variant(owner.pk, product_id=product.pk, sku="TAX-BROWSER", unit="piece", base_price="100", specifications=FRAME)
            save_fiscal_profile(owner.pk, data=data(), expected_version=0, operation_key=uuid.uuid4(), reason="Synthetic browser")
            revise_treatment(owner.pk, variant_id=self.variant.pk, expected_version=0, valid_from="2026-11-11", state="reviewed", category="S", basis="Synthetic browser review", operation_key=uuid.uuid4(), reason="Synthetic browser")

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def fill_header(self, page):
        await page.locator("#id_branch_id").select_option(self.branch_id)
        await page.locator("#id_as_of").fill("2026-11-11")
        await page.locator("#id_reason").fill("معاينة تجريبية")

    async def fill_line(self, page, number):
        await page.locator(f"#id_lines-{number}-sku").fill("TAX-BROWSER")
        await page.locator(f"#id_lines-{number}-quantity").fill("1")
        await page.locator(f"#id_lines-{number}-price_basis").select_option("gross")
        await page.locator(f"#id_lines-{number}-unit_amount").fill("115")
        await page.locator(f"#id_lines-{number}-discount_kind").select_option("percent")
        await page.locator(f"#id_lines-{number}-discount_value").fill("10")

    async def test_desktop_quote_and_append_only_classification_history(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.sign_in(page)
            await page.goto(self.live_server_url + "/sales/quotes/new/")
            await self.fill_header(page)
            await self.fill_line(page, 0)
            await page.locator("#id_document_discount_value").fill("11.50")
            await page.get_by_role("button", name="حساب وحفظ المعاينة", exact=True).click()
            await expect(page.get_by_role("heading", name="معاينة محفوظة", exact=True)).to_be_visible()
            await expect(page.locator("dd strong")).to_have_text("92.00")
            url = page.url
            await page.screenshot(path=str(fixtures.ARTIFACTS / "retail-tax-desktop.png"), full_page=True)
            await page.goto(self.live_server_url + f"/sales/taxes/{self.variant.pk}/")
            await page.locator("#id_valid_from").fill("2026-11-12")
            await page.locator("#id_state").select_option("blocked")
            await page.locator("#id_basis").fill("مراجعة جديدة معلقة")
            await page.locator("#id_reason").fill("حظر تجريبي")
            await page.get_by_role("button", name="حفظ إصدار التصنيف", exact=True).click()
            await expect(page.get_by_text("حظر تجريبي", exact=False)).to_be_visible()
            await page.goto(url)
            await expect(page.locator("dd strong")).to_have_text("92.00")
            await browser.close()

    async def test_phone_without_javascript_multiple_lines_and_order_discount(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            await self.sign_in(page)
            await page.goto(self.live_server_url + "/sales/quotes/new/")
            await self.fill_header(page)
            await self.fill_line(page, 0)
            await page.get_by_role("button", name="إضافة بند", exact=True).click()
            await expect(page.locator("#id_lines-0-unit_amount")).to_have_value("115")
            await self.fill_line(page, 1)
            await page.locator("#id_document_discount_value").fill("23")
            await page.screenshot(path=str(fixtures.ARTIFACTS / "retail-tax-phone-form.png"), full_page=True)
            await page.get_by_role("button", name="حساب وحفظ المعاينة", exact=True).click()
            await expect(page.get_by_role("heading", name="معاينة محفوظة", exact=True)).to_be_visible()
            await expect(page.locator("dd strong")).to_have_text("184.00")
            self.assertEqual(await page.locator("html").get_attribute("dir"), "rtl")
            self.assertLessEqual(await page.locator("body").evaluate("el => el.scrollWidth"), 390)
            await page.screenshot(path=str(fixtures.ARTIFACTS / "retail-tax-phone.png"), full_page=True)
            await browser.close()
