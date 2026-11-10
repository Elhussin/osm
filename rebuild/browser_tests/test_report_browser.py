from pathlib import Path
import re
import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from finance.journals import save_journal_draft, act_on_journal_draft, reverse_journal
from browser_tests import test_journal_browser as fixtures

ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class LedgerReportBrowserTests(StaticLiveServerTestCase):
    sign_in = fixtures.JournalBrowserTests.sign_in

    def setUp(self):
        fixtures.JournalBrowserTests.setUp(self)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            draft = save_journal_draft(owner.pk, branch_id=self.main_id, entry_date="2026-11-30", description="حركة التقرير التجريبية", lines=[dict(account_code="1001", debit="123.45", credit="0"), dict(account_code="3001", debit="0", credit="123.45")], operation_key=uuid.uuid4(), reason="Synthetic report fixture").draft
            entry = act_on_journal_draft(owner.pk, draft_id=draft.pk, action="post", expected_version=1, operation_key=uuid.uuid4(), reason="Synthetic report posting").entry
            reverse_journal(owner.pk, entry_id=entry.pk, entry_date="2026-12-01", operation_key=uuid.uuid4(), reason="Synthetic report reversal")

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def test_desktop_trial_balance_search_drilldown_and_source(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.sign_in(page, username="accountant")
            await page.goto(self.live_server_url + "/finance/reports/trial-balance/?starts_on=2026-11-01&ends_on=2026-11-30")
            await expect(page.get_by_role("heading", name="ميزان المراجعة والمطابقة", exact=True)).to_be_visible()
            await expect(page.get_by_text("المجاميع متطابقة ومتوازنة", exact=False)).to_be_visible()
            await expect(page.get_by_label("الفرع", exact=True).locator("option")).to_have_count(2)
            await page.get_by_label("بحث الحساب", exact=True).fill("1001")
            await page.get_by_role("button", name="بحث", exact=True).click()
            table = page.locator('[aria-label="ميزان المراجعة"]')
            await expect(table.locator("tbody tr")).to_have_count(1)
            await expect(table).to_contain_text(re.compile(r"123[.,]45"))
            await page.screenshot(path=str(ARTIFACTS / "trial-balance-desktop.png"), full_page=True)
            await table.get_by_role("link").click()
            await expect(page.get_by_role("heading", name="دفتر الحساب", exact=True)).to_be_visible()
            movements = page.locator('[aria-label="حركات الحساب"]')
            await expect(movements.locator("tbody tr")).to_have_count(1)
            await movements.get_by_role("link").click()
            await expect(page.get_by_text("حركة التقرير التجريبية", exact=True)).to_be_visible()
            self.assertNotIn(self.hidden_entry, page.url)
            await browser.close()

    async def test_mobile_nojs_opening_reversal_and_invalid_filters(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.sign_in(page, username="accountant")
            await page.goto(self.live_server_url + "/finance/reports/ledger/?account_code=1001&starts_on=2026-12-01&ends_on=2026-12-31")
            await expect(page.get_by_role("heading", name="دفتر الحساب", exact=True)).to_be_visible()
            await expect(page.get_by_text("الافتتاحي:", exact=False)).to_contain_text(re.compile(r"123[.,]45"))
            table = page.locator('[aria-label="حركات الحساب"]')
            await expect(table.locator("tbody tr")).to_have_count(1)
            await expect(table).to_contain_text("عكس")
            self.assertGreaterEqual((await page.get_by_label("الفرع", exact=True).bounding_box())["width"], 240)
            self.assertLessEqual(await page.locator("body").evaluate("el => el.scrollWidth"), 390)
            await page.screenshot(path=str(ARTIFACTS / "ledger-mobile-nojs.png"), full_page=True)
            await page.get_by_label("إلى تاريخ", exact=True).fill("2026-11-01")
            await page.get_by_role("button", name="عرض التقرير", exact=True).click()
            await expect(page.get_by_text("نهاية المدة تسبق بدايتها.", exact=True)).to_be_visible()
            await expect(page.locator('[aria-label="حركات الحساب"]')).to_have_count(0)
            await browser.close()
