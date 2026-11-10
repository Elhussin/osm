from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from access.services import create_member, assign_role
from browser_tests import test_workspace_browser as fixtures

ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccountingSetupBrowserTests(StaticLiveServerTestCase):
    sign_in = fixtures.WorkspaceBrowserTests.sign_in

    def setUp(self):
        fixtures.WorkspaceBrowserTests.setUp(self)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            accountant = create_member(owner.pk, username="accountant", password=fixtures.PASSWORD)
            assign_role(owner.pk, user_id=accountant.pk, role_code="accountant")

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def account(self, page, code, name, *, parent=None, group=False, side="debit"):
        await page.goto(self.live_server_url + "/finance/accounts/new/")
        await page.get_by_label("رمز الحساب", exact=True).fill(code)
        await page.get_by_label("اسم الحساب", exact=True).fill(name)
        await page.get_by_label("تصنيف الحساب", exact=True).select_option("asset")
        await page.get_by_label("طبيعة الرصيد", exact=True).select_option(side)
        await page.get_by_label("نوع الحساب", exact=True).select_option("group" if group else "posting")
        if parent:
            await page.get_by_label("رمز المجموعة الأب (اختياري)", exact=True).fill(parent)
        await page.get_by_label("السبب", exact=True).fill("إعداد دليل صناعي للاختبار")
        await page.get_by_role("button", name="حفظ الحساب", exact=True).click()
        await expect(page.get_by_role("heading", name=name, exact=True)).to_be_visible()
        return page.url

    async def change(self, page, action, name=None):
        await page.get_by_label("الإجراء", exact=True).select_option(action)
        if name:
            await page.get_by_label("الاسم الجديد (عند تغيير الاسم)", exact=True).fill(name)
        await page.get_by_label("السبب", exact=True).fill("تغيير صناعي موثق")
        await page.get_by_role("button", name="حفظ تغيير الحساب", exact=True).click()

    async def test_desktop_chart_hierarchy_rename_disable_and_activation(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            await self.sign_in(page)
            await page.locator(".sidebar").get_by_role("link", name="المحاسبة", exact=True).click()
            await expect(page.get_by_role("heading", name="دليل الحسابات", exact=True)).to_be_visible()
            root_url = await self.account(page, "1000", "أصول اختبارية", group=True)
            child_url = await self.account(page, "1100", "حساب مقابل تجريبي", parent="1000", side="credit")
            await self.change(page, "rename", "حساب مقابل مصحح")
            await expect(page.get_by_role("heading", name="حساب مقابل مصحح", exact=True)).to_be_visible()
            await expect(page.locator("tbody")).to_contain_text("حساب مقابل تجريبي")
            await page.goto(root_url)
            await self.change(page, "disable")
            await expect(page.get_by_role("alert")).to_contain_text("عطّل الحسابات الفرعية النشطة")
            await page.goto(child_url)
            await self.change(page, "disable")
            await expect(page.get_by_text("حُفظ تغيير الحساب وتاريخه.", exact=True)).to_be_visible()
            await page.goto(root_url)
            await self.change(page, "disable")
            await expect(page.get_by_text("حُفظ تغيير الحساب وتاريخه.", exact=True)).to_be_visible()
            await self.change(page, "activate")
            await expect(page.locator("tbody")).to_contain_text("تفعيل حساب")
            await page.goto(child_url)
            await self.change(page, "activate")
            await page.goto(self.live_server_url + "/finance/accounts/?q=1100")
            await expect(page.get_by_role("link", name="حساب مقابل مصحح", exact=True)).to_be_visible()
            await expect(page.locator("tbody")).to_contain_text("1000/1100")
            await page.wait_for_load_state("load")
            await page.screenshot(path=str(ARTIFACTS / "accounting-chart-desktop.png"), full_page=True)
            await context.close()
            await browser.close()

    async def period(self, page, code, name, start, end):
        await page.goto(self.live_server_url + "/finance/periods/new/")
        for label, value in (("رمز الفترة", code), ("اسم الفترة", name), ("بداية الفترة", start), ("نهاية الفترة", end), ("السبب", "إعداد فترة صناعية")):
            await page.get_by_label(label, exact=True).fill(value)
        await page.get_by_role("button", name="حفظ الفترة", exact=True).click()

    async def test_mobile_nojs_accountant_period_overlap_close_and_reopen(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.sign_in(page, username="accountant")
            await self.period(page, "2026-11", "فترة نوفمبر التجريبية", "2026-11-01", "2026-11-30")
            await expect(page.get_by_role("heading", name="فترة نوفمبر التجريبية", exact=True)).to_be_visible()
            original = page.url
            await self.period(page, "OVERLAP", "فترة متداخلة", "2026-11-30", "2026-12-31")
            await expect(page.get_by_role("alert")).to_contain_text("يتداخل مع فترة محفوظة")
            await page.goto(original)
            await page.get_by_label("السبب", exact=True).fill("إغلاق صناعي للاختبار")
            await page.get_by_role("button", name="إغلاق الفترة", exact=True).click()
            await expect(page.locator("strong").filter(has_text="مغلقة")).to_be_visible()
            await page.get_by_label("السبب", exact=True).fill("إعادة فتح صناعية موثقة")
            await page.get_by_role("button", name="إعادة فتح الفترة", exact=True).click()
            await expect(page.locator("tbody")).to_contain_text("إعادة فتح فترة")
            self.assertEqual(await page.locator("tbody tr").count(), 3)
            await page.wait_for_load_state("load")
            self.assertLessEqual(await page.locator("body").evaluate("e => e.scrollWidth"), 390)
            await page.screenshot(path=str(ARTIFACTS / "accounting-period-mobile-nojs.png"), full_page=True)
            await self.period(page, "2026-12", "فترة ديسمبر التجريبية", "2026-12-01", "2026-12-31")
            await expect(page.get_by_role("heading", name="فترة ديسمبر التجريبية", exact=True)).to_be_visible()
            await context.close()
            denied = await browser.new_context()
            page = await denied.new_page()
            await self.sign_in(page, username="sara")
            response = await page.goto(self.live_server_url + "/finance/periods/")
            self.assertEqual(response.status, 403)
            await denied.close()
            await browser.close()
