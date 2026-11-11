from pathlib import Path
import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from access.models import Branch
from access.services import create_branch, create_member, assign_role, grant_branch_access
from finance.setup_services import create_account
from sales.registers import create_register
from browser_tests import test_workspace_browser as fixtures

ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CashRegisterBrowserTests(StaticLiveServerTestCase):
    sign_in = fixtures.WorkspaceBrowserTests.sign_in

    def setUp(self):
        fixtures.WorkspaceBrowserTests.setUp(self)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            main = Branch.objects.get(code="MAIN")
            self.main_id = str(main.pk)
            other = create_branch(owner.pk, code="OTHER", name="فرع محجوب تجريبي")
            manager = create_member(owner.pk, username="register-admin", password=fixtures.PASSWORD)
            assign_role(owner.pk, user_id=manager.pk, role_code="company_admin")
            assign_role(owner.pk, user_id=manager.pk, role_code="accountant")
            grant_branch_access(owner.pk, user_id=manager.pk, branch_id=main.pk)
            for code in ("1101", "1102", "1103"):
                create_account(owner.pk, code=code, name="نقدية الصندوق التجريبي " + code, kind="asset", normal_side="debit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic register chart")
            self.hidden = str(create_register(owner.pk, branch_id=other.pk, code="HIDDEN", name="صندوق فرع محجوب", cash_account_code="1103", operation_key=uuid.uuid4(), reason="Synthetic hidden register").register_id)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def fill(self, page, code="POS-1", account="1101"):
        await page.get_by_label("فرع الصندوق", exact=True).select_option(self.main_id)
        await page.get_by_label("رمز الصندوق", exact=True).fill(code)
        await page.get_by_label("اسم الصندوق", exact=True).fill("صندوق تجريبي رئيسي")
        await page.get_by_label("رمز حساب النقدية", exact=True).fill(account)
        await page.get_by_label("سبب الإعداد", exact=True).fill("تهيئة صندوق للاختبار")
        await page.get_by_role("button", name="حفظ الصندوق", exact=True).click()

    async def test_desktop_configuration_history_scope_search_and_cashier_denial(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.sign_in(page, username="register-admin")
            await page.locator(".sidebar").get_by_role("link", name="صناديق البيع", exact=True).click()
            await page.get_by_role("link", name="إضافة صندوق بيع", exact=True).click()
            await expect(page.get_by_label("فرع الصندوق", exact=True).locator("option")).to_have_count(2)
            await self.fill(page)
            await expect(page.get_by_role("heading", name="صندوق تجريبي رئيسي", exact=True)).to_be_visible()
            await page.get_by_label("الاسم الجديد (عند تغيير الاسم)", exact=True).fill("صندوق الاستقبال")
            await page.get_by_label("سبب التغيير", exact=True).fill("تسمية موثقة للاختبار")
            await page.get_by_role("button", name="حفظ تغيير الصندوق", exact=True).click()
            await expect(page.get_by_role("heading", name="صندوق الاستقبال", exact=True)).to_be_visible()
            await expect(page.locator('[aria-label="تاريخ إعداد الصندوق"] tbody tr')).to_have_count(2)
            await page.screenshot(path=str(ARTIFACTS / "register-desktop-history.png"), full_page=True)
            await page.get_by_role("link", name="صناديق البيع", exact=True).last.click()
            await page.get_by_label("بحث الصندوق أو الفرع", exact=True).fill("الاستقبال")
            await page.get_by_role("button", name="بحث", exact=True).click()
            await expect(page.locator('[aria-label="صناديق البيع"] tbody tr')).to_have_count(1)
            response = await page.goto(self.live_server_url + f"/sales/registers/{self.hidden}/")
            self.assertEqual(response.status, 404)
            limited = await browser.new_page()
            await self.sign_in(limited, username="sara")
            self.assertEqual((await limited.goto(self.live_server_url + "/sales/registers/new/")).status, 403)
            await browser.close()

    async def test_mobile_nojs_duplicate_account_rejection_disable_and_activate(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.sign_in(page, username="register-admin")
            await page.goto(self.live_server_url + "/sales/registers/new/")
            await self.fill(page)
            register_url = page.url
            await page.goto(self.live_server_url + "/sales/registers/new/")
            await self.fill(page, code="POS-2")
            await expect(page.get_by_text("حساب النقدية مخصص لصندوق آخر؛ اختر حسابًا مستقلًا.", exact=True)).to_be_visible()
            await page.get_by_label("رمز حساب النقدية", exact=True).fill("1102")
            await page.get_by_role("button", name="حفظ الصندوق", exact=True).click()
            await expect(page.get_by_role("heading", name="صندوق تجريبي رئيسي", exact=True)).to_be_visible()
            await page.goto(register_url)
            for action in ("disable", "activate"):
                await page.get_by_label("الإجراء", exact=True).select_option(action)
                await page.get_by_label("سبب التغيير", exact=True).fill("تغيير حالة الصندوق للاختبار")
                await page.get_by_role("button", name="حفظ تغيير الصندوق", exact=True).click()
            await expect(page.locator('[aria-label="تاريخ إعداد الصندوق"] tbody tr')).to_have_count(3)
            self.assertLessEqual(await page.locator("body").evaluate("el => el.scrollWidth"), 390)
            await page.screenshot(path=str(ARTIFACTS / "register-mobile-nojs.png"), full_page=True)
            await browser.close()
