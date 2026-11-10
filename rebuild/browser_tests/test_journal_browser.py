from pathlib import Path
import re
import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from access.models import Branch
from access.services import create_branch, create_member, assign_role, grant_branch_access
from finance.setup_services import create_account, create_period
from finance.journals import save_journal_draft, act_on_journal_draft
from browser_tests import test_workspace_browser as fixtures

ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class JournalBrowserTests(StaticLiveServerTestCase):
    sign_in = fixtures.WorkspaceBrowserTests.sign_in

    def setUp(self):
        fixtures.WorkspaceBrowserTests.setUp(self)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            main = Branch.objects.get(code="MAIN")
            self.main_id = str(main.pk)
            other = create_branch(owner.pk, code="OTHER", name="فرع غير مصرح للمحاسب")
            accountant = create_member(owner.pk, username="accountant", password=fixtures.PASSWORD)
            assign_role(owner.pk, user_id=accountant.pk, role_code="accountant")
            grant_branch_access(owner.pk, user_id=accountant.pk, branch_id=main.pk)
            cash = create_account(owner.pk, code="1001", name="نقد تجريبي وقت الترحيل", kind="asset", normal_side="debit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic chart").account
            self.cash_id = str(cash.pk)
            create_account(owner.pk, code="3001", name="رأس مال تجريبي", kind="equity", normal_side="credit", is_group=False, operation_key=uuid.uuid4(), reason="Synthetic chart")
            self.period_ids = {}
            for code, start, end, name in (("2026-11", "2026-11-01", "2026-11-30", "نوفمبر التجريبي"), ("2026-12", "2026-12-01", "2026-12-31", "ديسمبر التجريبي"), ("2027-01", "2027-01-01", "2027-01-31", "فترة غير مستخدمة")):
                period = create_period(owner.pk, code=code, name=name, starts_on=start, ends_on=end, operation_key=uuid.uuid4(), reason="Synthetic period").period
                self.period_ids[code] = str(period.pk)
            hidden = save_journal_draft(owner.pk, branch_id=other.pk, entry_date="2026-11-15", description="قيد فرع سري للاختبار", lines=[{"account_code": "1001", "debit": "50", "credit": "0"}, {"account_code": "3001", "debit": "0", "credit": "50"}], operation_key=uuid.uuid4(), reason="Synthetic hidden draft").draft
            self.hidden_id = str(hidden.pk)
            entry = act_on_journal_draft(owner.pk, draft_id=hidden.pk, action="post", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic hidden posting").entry
            self.hidden_entry = str(entry.pk)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def begin(self, page, *, credit="100", third=False):
        await page.goto(self.live_server_url + "/finance/journals/new/")
        await page.get_by_label("فرع القيد", exact=True).select_option(self.main_id)
        await page.get_by_label("تاريخ القيد", exact=True).fill("2026-11-15")
        await page.get_by_label("بيان القيد", exact=True).fill("قيد محاسبي صناعي")
        await page.get_by_label("سبب حفظ الإصدار", exact=True).fill("إعداد قيد للاختبار")
        await page.get_by_label("رمز الحساب — السطر 1", exact=True).fill("1001")
        await page.get_by_label("مدين — السطر 1", exact=True).fill("100")
        await page.get_by_label("رمز الحساب — السطر 2", exact=True).fill("3001")
        await page.get_by_label("دائن — السطر 2", exact=True).fill("60" if third else credit)
        if third:
            await page.get_by_role("button", name="إضافة سطر", exact=True).click()
            await expect(page.get_by_label("بيان القيد", exact=True)).to_have_value("قيد محاسبي صناعي")
            await page.get_by_label("رمز الحساب — السطر 3", exact=True).fill("3001")
            await page.get_by_label("دائن — السطر 3", exact=True).fill("40")
        await page.get_by_role("button", name="حفظ المسودة", exact=True).click()
        await expect(page.get_by_role("heading", name="مسودة قيد", exact=True)).to_be_visible()
        return page.url

    async def post(self, page):
        await page.get_by_label("سبب الترحيل", exact=True).fill("ترحيل صناعي موثق")
        await page.get_by_role("button", name="ترحيل القيد", exact=True).click()

    async def reverse(self, page, day):
        await page.get_by_text("عكس القيد", exact=True).click()
        await page.get_by_label("تاريخ القيد العكسي", exact=True).fill(day)
        await page.get_by_label("سبب العكس", exact=True).fill("عكس صناعي للمراجعة")
        await page.get_by_role("button", name="اعتماد العكس", exact=True).click()
        await expect(page.get_by_role("heading", name=re.compile(r"^JE-"))).to_be_visible()

    async def test_desktop_revision_unbalanced_rejection_post_snapshot_and_later_reversal(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            await self.sign_in(page)
            await page.locator(".sidebar").get_by_role("link", name="المحاسبة", exact=True).click()
            await page.get_by_role("link", name="القيود المحاسبية", exact=True).click()
            draft_url = await self.begin(page, credit="90")
            await self.post(page)
            await expect(page.get_by_role("alert")).to_contain_text("تساوى المدين والدائن")
            await page.get_by_role("link", name="تعديل المسودة", exact=True).click()
            await page.get_by_label("دائن — السطر 2", exact=True).fill("100")
            await page.get_by_label("سبب حفظ الإصدار", exact=True).fill("تصحيح التوازن")
            await page.get_by_role("button", name="حفظ المسودة", exact=True).click()
            await expect(page.get_by_role("heading", name="مسودة قيد", exact=True)).to_be_visible()
            await self.post(page)
            await expect(page.get_by_role("heading", name=re.compile(r"^JE-"))).to_be_visible()
            original = page.url
            await page.goto(self.live_server_url + f"/finance/accounts/{self.cash_id}/")
            await page.get_by_label("الاسم الجديد (عند تغيير الاسم)", exact=True).fill("اسم جديد بعد الترحيل")
            await page.get_by_label("السبب", exact=True).fill("تغيير وصف الدليل")
            await page.get_by_role("button", name="حفظ تغيير الحساب", exact=True).click()
            await page.goto(original)
            await expect(page.get_by_role("table", name="أسطر القيد المرحل", exact=True)).to_contain_text("نقد تجريبي وقت الترحيل")
            await expect(page.get_by_role("table", name="أسطر القيد المرحل", exact=True)).not_to_contain_text("اسم جديد بعد الترحيل")
            await page.goto(self.live_server_url + f"/finance/periods/{self.period_ids['2026-11']}/")
            await page.get_by_label("السبب", exact=True).fill("إغلاق الفترة الأصلية")
            await page.get_by_role("button", name="إغلاق الفترة", exact=True).click()
            await page.goto(original)
            await self.reverse(page, "2026-12-01")
            await expect(page.get_by_role("table", name="أسطر القيد المرحل", exact=True)).to_contain_text("نقد تجريبي وقت الترحيل")
            await page.goto(original)
            await expect(page.get_by_text("عُكس بالقيد", exact=False)).to_be_visible()
            await page.wait_for_load_state("load")
            await page.screenshot(path=str(ARTIFACTS / "journal-posted-desktop.png"), full_page=True)
            response = await page.goto(draft_url + "edit/")
            self.assertEqual(response.status, 404)
            await context.close()
            await browser.close()

    async def test_mobile_nojs_add_line_post_and_reverse(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.sign_in(page, username="accountant")
            await self.begin(page, third=True)
            await self.post(page)
            await expect(page.get_by_role("heading", name=re.compile(r"^JE-"))).to_be_visible()
            self.assertEqual(await page.get_by_role("table", name="أسطر القيد المرحل", exact=True).locator("tbody tr").count(), 3)
            await self.reverse(page, "2026-11-16")
            await page.wait_for_load_state("load")
            self.assertLessEqual(await page.locator("body").evaluate("e => e.scrollWidth"), 390)
            await page.screenshot(path=str(ARTIFACTS / "journal-reversal-mobile-nojs.png"), full_page=True)
            await context.close()
            await browser.close()

    async def test_draft_cancel_unused_period_void_replacement_and_branch_scope(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.sign_in(page, username="accountant")
            await self.begin(page)
            await page.get_by_text("إلغاء المسودة دون حذف تاريخها", exact=True).click()
            await page.get_by_label("سبب إلغاء المسودة", exact=True).fill("إلغاء صناعي موثق")
            await page.get_by_role("button", name="إلغاء المسودة", exact=True).click()
            self.assertEqual(await page.get_by_role("button", name="ترحيل القيد", exact=True).count(), 0)
            await expect(page.get_by_role("heading", name="إصدارات المسودة", exact=True)).to_be_visible()
            for path in (f"/finance/journals/{self.hidden_id}/", f"/finance/entries/{self.hidden_entry}/"):
                response = await page.goto(self.live_server_url + path)
                self.assertEqual(response.status, 404)
            await page.goto(self.live_server_url + f"/finance/periods/{self.period_ids['2027-01']}/")
            await page.get_by_label("سبب إلغاء الفترة", exact=True).fill("تصحيح فترة لم تستخدم")
            await page.get_by_role("button", name="إلغاء الفترة غير المستخدمة", exact=True).click()
            await expect(page.locator("strong").filter(has_text="ملغاة")).to_be_visible()
            self.assertEqual(await page.get_by_role("button", name="إعادة فتح الفترة", exact=True).count(), 0)
            await page.goto(self.live_server_url + "/finance/periods/new/")
            for label, value in (("رمز الفترة", "2027-01-NEW"), ("اسم الفترة", "فترة بديلة موثقة"), ("بداية الفترة", "2027-01-01"), ("نهاية الفترة", "2027-01-31"), ("السبب", "تصحيح الفترة الملغاة")):
                await page.get_by_label(label, exact=True).fill(value)
            await page.get_by_role("button", name="حفظ الفترة", exact=True).click()
            await expect(page.get_by_role("heading", name="فترة بديلة موثقة", exact=True)).to_be_visible()
            await page.goto(self.live_server_url + f"/finance/periods/{self.period_ids['2026-11']}/")
            await page.get_by_label("سبب إلغاء الفترة", exact=True).fill("محاولة إلغاء فترة مستخدمة")
            await page.get_by_role("button", name="إلغاء الفترة غير المستخدمة", exact=True).click()
            await expect(page.get_by_role("alert")).to_contain_text("مرتبطة بأي إصدار قيد")
            await context.close()
            await browser.close()
