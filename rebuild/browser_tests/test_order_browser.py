import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from clinical.services import create_customer
from finance.setup_services import create_account
from inventory.receiving import receive_stock
from sales.registers import create_register
from sales.shifts import open_shift
from . import test_tax_browser as tax_fixture
from . import test_workspace_browser as fixtures


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CashOrderBrowserTests(StaticLiveServerTestCase):
    sign_in = fixtures.WorkspaceBrowserTests.sign_in

    def setUp(self):
        tax_fixture.RetailTaxBrowserTests.setUp(self)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            self.customer = create_customer(owner.pk, branch_id=self.branch_id, first_name="عميل طلب تجريبي")
            account = create_account(owner.pk, code="1118", name="Synthetic cash", kind="asset", normal_side="debit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic setup").account
            register = create_register(owner.pk, branch_id=self.branch_id, code="BROWSER", name="صندوق الطلبات", cash_account_code=account.code, operation_key=uuid.uuid4(), reason="Synthetic setup").register
            self.shift = open_shift(owner.pk, register_id=register.pk, opening_cash="100", operation_key=uuid.uuid4(), reason="Synthetic custody").shift
            receive_stock(owner.pk, branch_id=self.branch_id, variant_id=self.variant.pk, quantity=2, operation_key=uuid.uuid4(), reason="Synthetic stock")

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def draft(self, page):
        await page.goto(self.live_server_url + f"/customers/{self.customer.pk}/")
        await page.get_by_role("link", name="تسعير طلب بيع", exact=True).click()
        await page.locator("#id_branch_id").select_option(self.branch_id)
        await page.locator("#id_reason").fill("طلب تجريبي")
        await page.locator("#id_lines-0-sku").fill("TAX-BROWSER")
        await page.locator("#id_lines-0-unit_amount").fill("115")
        await page.get_by_role("button", name="حساب وحفظ المعاينة", exact=True).click()
        await page.get_by_role("link", name="إنشاء طلب من المعاينة", exact=True).click()
        await page.locator("#id_shift_id").select_option(str(self.shift.pk))
        await page.locator("#id_reason").fill("مراجعة تجريبية")
        await page.get_by_role("button", name="حفظ مسودة الطلب", exact=True).click()
        await expect(page.get_by_role("heading", name="طلب بيع", exact=True)).to_be_visible()

    async def test_desktop_review_reprice_confirm_and_cancel(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.sign_in(page)
            await self.draft(page)
            await page.get_by_role("link", name="تعديل التسعير", exact=True).click()
            await page.locator("#id_lines-0-unit_amount").fill("230")
            await page.locator("#id_reason").fill("إعادة تسعير تجريبية")
            await page.get_by_role("button", name="حساب وحفظ المعاينة", exact=True).click()
            await page.locator("#id_reason").fill("تحديث التسعير")
            await page.get_by_role("button", name="حفظ مسودة الطلب", exact=True).click()
            await page.locator("#id_reason").fill("اعتماد الطلب")
            await page.get_by_role("button", name="تنفيذ الإجراء", exact=True).click()
            await expect(page.get_by_text("مؤكد", exact=True)).to_be_visible()
            await expect(page.locator("#id_action")).to_have_value("cancel")
            await expect(page.get_by_text("المطلوب 230.00 SAR", exact=True)).to_be_visible()
            await page.screenshot(path=str(fixtures.ARTIFACTS / "cash-order-desktop-confirmed.png"), full_page=True)
            await page.locator("#id_action").select_option("cancel")
            await page.locator("#id_reason").fill("إلغاء تجريبي")
            await page.get_by_role("button", name="تنفيذ الإجراء", exact=True).click()
            await expect(page.get_by_text("ملغى", exact=True)).to_be_visible()
            await browser.close()

    async def test_phone_without_javascript_customer_without_identifier(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            await self.sign_in(page)
            await self.draft(page)
            await expect(page.get_by_text("دون وصفة مرتبطة.", exact=True)).to_be_visible()
            await page.locator("#id_reason").fill("اعتماد الهاتف")
            await page.get_by_role("button", name="تنفيذ الإجراء", exact=True).click()
            await expect(page.get_by_text("مؤكد", exact=True)).to_be_visible()
            await expect(page.locator("#id_action")).to_have_value("cancel")
            self.assertLessEqual(await page.locator("body").evaluate("el => el.scrollWidth"), 390)
            await page.screenshot(path=str(fixtures.ARTIFACTS / "cash-order-phone-confirmed.png"), full_page=True)
            await browser.close()
