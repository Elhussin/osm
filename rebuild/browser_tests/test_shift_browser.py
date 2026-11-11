from pathlib import Path
import re
import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from sales.registers import create_register
from sales.shifts import open_shift
from browser_tests import test_register_browser as fixtures

ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class CashShiftBrowserTests(StaticLiveServerTestCase):
    sign_in = fixtures.CashRegisterBrowserTests.sign_in

    def setUp(self):
        fixtures.CashRegisterBrowserTests.setUp(self)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            self.register_id = str(create_register(owner.pk, branch_id=self.main_id, code="POS-1", name="صندوق العهدة التجريبي", cash_account_code="1101", operation_key=uuid.uuid4(), reason="Synthetic shift register").register_id)
            self.hidden_shift = str(open_shift(owner.pk, register_id=self.hidden, opening_cash="50", operation_key=uuid.uuid4(), reason="Synthetic hidden shift").shift_id)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def begin(self, page):
        await page.goto(self.live_server_url + "/sales/shifts/new/")
        await expect(page.get_by_label("الصندوق المتاح", exact=True).locator("option")).to_have_count(2)
        await page.get_by_label("الصندوق المتاح", exact=True).select_option(self.register_id)
        await page.get_by_label("العهدة الافتتاحية", exact=True).fill("100")
        await page.get_by_label("سبب فتح الوردية", exact=True).fill("عهدة افتتاحية صناعية")
        await page.get_by_role("button", name="فتح الوردية بعهدتي", exact=True).click()
        await expect(page.get_by_role("heading", name=re.compile(r"^وردية "))).to_be_visible()
        return page.url

    async def action(self, page, action, cash=None, recipient=None):
        await page.get_by_label("إجراء الوردية", exact=True).select_option(action)
        if cash is not None:
            await page.get_by_label("المبلغ المعدود", exact=True).fill(cash)
        if recipient:
            await page.get_by_label("اسم دخول المستلم", exact=True).fill(recipient)
        await page.get_by_label("سبب العملية", exact=True).fill("عملية عهدة صناعية موثقة")
        await page.get_by_role("button", name="تنفيذ إجراء الوردية", exact=True).click()

    async def test_desktop_two_sessions_handover_acceptance_and_balanced_close(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            outgoing = await browser.new_context(viewport={"width": 1440, "height": 1000})
            incoming = await browser.new_context(viewport={"width": 1440, "height": 1000})
            source = await outgoing.new_page()
            target = await incoming.new_page()
            await self.sign_in(source, username="sara")
            shift_url = await self.begin(source)
            await self.action(source, "request_handover", "100", "ahmed")
            await expect(source.get_by_text("تسليم معلق إلى", exact=False)).to_contain_text("ahmed")
            await self.sign_in(target, username="ahmed")
            await target.goto(shift_url)
            await self.action(target, "accept_handover", "100")
            await expect(target.get_by_text("حائز العهدة:", exact=False)).to_contain_text("ahmed")
            await source.reload()
            await expect(source.get_by_role("button", name="تنفيذ إجراء الوردية", exact=True)).to_have_count(0)
            await self.action(target, "submit_count", "100")
            await expect(target.get_by_role("heading", name="مغلقة", exact=True)).to_be_visible()
            await expect(target.locator('[aria-label="تاريخ العهدة والجرد"] tbody tr')).to_have_count(4)
            await target.screenshot(path=str(ARTIFACTS / "shift-desktop-handover-closed.png"), full_page=True)
            self.assertEqual((await target.goto(self.live_server_url + f"/sales/shifts/{self.hidden_shift}/")).status, 404)
            await browser.close()

    async def test_mobile_nojs_variance_review_disable_guard_and_supervisor_approval(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            cashier_context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            manager_context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            cashier = await cashier_context.new_page()
            manager = await manager_context.new_page()
            await self.sign_in(cashier, username="sara")
            shift_url = await self.begin(cashier)
            await self.action(cashier, "request_handover", "100", "ahmed")
            await self.action(cashier, "cancel_handover")
            await self.action(cashier, "submit_count", "97")
            await expect(cashier.get_by_role("heading", name="بانتظار اعتماد فرق الجرد", exact=True)).to_be_visible()
            await expect(cashier.get_by_role("button", name="تنفيذ إجراء الوردية", exact=True)).to_have_count(0)
            self.assertLessEqual(await cashier.locator("body").evaluate("el => el.scrollWidth"), 390)
            await self.sign_in(manager, username="register-admin")
            await manager.goto(self.live_server_url + f"/sales/registers/{self.register_id}/")
            await manager.get_by_label("الإجراء", exact=True).select_option("disable")
            await manager.get_by_label("سبب التغيير", exact=True).fill("اختبار منع تعطيل عهدة غير مغلقة")
            await manager.get_by_role("button", name="حفظ تغيير الصندوق", exact=True).click()
            await expect(manager.get_by_text("لا يمكن تعطيل صندوق له وردية غير مغلقة أو تسليم معلق.", exact=True)).to_be_visible()
            await manager.goto(shift_url)
            await self.action(manager, "approve_variance")
            await expect(manager.get_by_role("heading", name="مغلقة", exact=True)).to_be_visible()
            await expect(manager.get_by_text("فرق المعدود عن المتوقع:", exact=False)).to_contain_text("-3")
            self.assertLessEqual(await manager.locator("body").evaluate("el => el.scrollWidth"), 390)
            await manager.screenshot(path=str(ARTIFACTS / "shift-mobile-nojs-approved.png"), full_page=True)
            await browser.close()
