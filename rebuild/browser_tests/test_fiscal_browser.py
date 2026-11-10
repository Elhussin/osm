from pathlib import Path
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from playwright.async_api import async_playwright, expect
from browser_tests import test_workspace_browser as fixtures

ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FiscalBrowserTests(StaticLiveServerTestCase):
    setUp = fixtures.WorkspaceBrowserTests.setUp
    sign_in = fixtures.WorkspaceBrowserTests.sign_in

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def test_desktop_fiscal_registered_setup_remains_disconnected(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            await self.sign_in(page)
            await page.locator(".sidebar").get_by_role("link", name="الملف الضريبي", exact=True).click()
            await expect(page.get_by_role("heading", name="الملف الضريبي والاستعداد للربط", exact=True)).to_be_visible()
            values = {"الاسم القانوني للمنشأة": "بصريات اختبار ضريبي", "رقم ضريبة القيمة المضافة": "300000000000003", "السجل التجاري": "SYNTHETIC-CR",
                "الشارع": "شارع تجريبي", "رقم المبنى": "1234", "الرقم الإضافي": "5678", "الحي": "حي تجريبي", "المدينة": "مدينة تجريبية", "الرمز البريدي": "12345", "سبب الإعداد أو التصحيح": "إعداد صناعي للاختبار"}
            await page.get_by_label("حالة تسجيل ضريبة القيمة المضافة", exact=True).select_option("registered")
            for label, value in values.items():
                await page.get_by_label(label, exact=True).fill(value)
            await page.get_by_role("button", name="حفظ إصدار الملف", exact=True).click()
            await expect(page.get_by_text("اكتملت حقول الإعداد الأولي. صحة التسجيل والربط لم تُختبر لدى الهيئة.", exact=True)).to_be_visible()
            await expect(page.get_by_text("الربط مع هيئة الزكاة والضريبة والجمارك غير مفعل.", exact=False)).to_be_visible()
            await expect(page.get_by_role("heading", name="تصحيح الملف — الإصدار الحالي 1", exact=True)).to_be_visible()
            await page.wait_for_load_state("load")
            await page.screenshot(path=str(ARTIFACTS / "fiscal-setup-desktop.png"), full_page=True)
            self.assertEqual(await page.get_by_role("button", name="إرسال للهيئة", exact=True).count(), 0)
            await context.close()
            await browser.close()

    async def test_mobile_nojs_draft_correction_and_unauthorized_cashier(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.sign_in(page)
            await page.goto(self.live_server_url + "/account/fiscal/")
            await page.get_by_label("الاسم القانوني للمنشأة", exact=True).fill("منشأة اختبار أولي")
            await page.get_by_label("سبب الإعداد أو التصحيح", exact=True).fill("حفظ بيانات أولية")
            await page.get_by_role("button", name="حفظ إصدار الملف", exact=True).click()
            await expect(page.get_by_text("يمكن حفظ البيانات الأولية ثم استكمال النواقص:", exact=True)).to_be_visible()
            await page.get_by_label("الاسم القانوني للمنشأة", exact=True).fill("منشأة اختبار مصححة")
            await page.get_by_label("سبب الإعداد أو التصحيح", exact=True).fill("تصحيح الاسم التجريبي")
            await page.get_by_role("button", name="حفظ إصدار الملف", exact=True).click()
            await expect(page.get_by_role("heading", name="تصحيح الملف — الإصدار الحالي 2", exact=True)).to_be_visible()
            history = page.locator("tbody")
            await expect(history).to_contain_text("منشأة اختبار أولي")
            await expect(history).to_contain_text("منشأة اختبار مصححة")
            await page.wait_for_load_state("load")
            self.assertLessEqual(await page.locator("body").evaluate("e => e.scrollWidth"), 390)
            await page.screenshot(path=str(ARTIFACTS / "fiscal-setup-mobile-nojs.png"), full_page=True)
            await context.close()
            cashier = await browser.new_context()
            page = await cashier.new_page()
            await self.sign_in(page, username="sara")
            response = await page.goto(self.live_server_url + "/account/fiscal/")
            self.assertEqual(response.status, 403)
            await cashier.close()
            await browser.close()
