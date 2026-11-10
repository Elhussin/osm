from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
import uuid
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from access.models import Branch
from access.services import create_branch, create_member, assign_role
from catalog.services import create_product, create_variant
from directory.provisioning import provision_company
from inventory.receiving import receive_stock

PASSWORD = "Synthetic-Tracking-Browser-2026!"
ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class TrackingBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        company = provision_company(name="بصريات تتبع تجريبية", domain="localhost", username="owner", password=PASSWORD,
            operation_key=uuid.uuid4(), grant_runtime=False)
        self.today = timezone.localdate()
        self.expiry = (self.today + timedelta(days=30)).isoformat()
        self.serial = "SN-" + "A" * 50
        with tenant_context(company):
            owner = get_user_model().objects.get(username="owner")
            main = Branch.objects.get(code="MAIN")
            self.main_id, self.main_name = str(main.pk), main.name
            other = create_branch(owner.pk, code="WAREHOUSE", name="المستودع التجريبي", kind="warehouse")
            self.other_id, self.other_name = str(other.pk), other.name
            clerk = create_member(owner.pk, username="clerk", password=PASSWORD)
            assign_role(owner.pk, user_id=clerk.pk, role_code="inventory_clerk", branch_id=main.pk)
            assign_role(owner.pk, user_id=clerk.pk, role_code="catalog_reader")
            self.ids = {}
            self.skus = {}
            cases = [("frame", "piece", {"color": "black", "eye_size": 52, "bridge": 18, "temple": 140}),
                ("device", "piece", {"specification": "V1"}),
                ("contact_lens", "box", {"material": "Hydrogel", "diameter": "14", "base_curve": "8.6", "sphere": "0", "pack_size": 30, "replacement": "monthly"})]
            for kind, unit, specs in cases:
                product = create_product(owner.pk, code_value=kind.upper(), name={"frame": "إطار تجريبي", "device": "جهاز تجريبي", "contact_lens": "لاصقة تجريبية"}[kind], kind=kind)
                variant = create_variant(owner.pk, product_id=product.pk, sku="UI-" + kind.upper(), unit=unit, base_price="20", specifications=specs)
                self.ids[kind], self.skus[kind] = str(variant.pk), variant.sku
            earlier = timezone.now() - timedelta(days=2)
            with patch("django.utils.timezone.now", return_value=earlier):
                receive_stock(owner.pk, branch_id=main.pk, variant_id=self.ids["contact_lens"], quantity=3,
                    operation_key=uuid.uuid4(), reason="Synthetic earlier receipt", lot_code="OLD-BATCH", expires_on=self.today - timedelta(days=1))
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

    async def receive(self, page, kind, quantity, *, lot=None, serial=None):
        await page.goto(self.live_server_url + f"/inventory/receiving/{self.ids[kind]}/")
        await page.get_by_label("الفرع / المستودع", exact=True).select_option(self.main_id)
        await page.get_by_label("الكمية المستلمة بوحدة الصنف", exact=True).fill(str(quantity))
        if lot:
            await page.get_by_label("رقم الدفعة", exact=True).fill(lot)
            await page.get_by_label("تاريخ الصلاحية", exact=True).fill(self.expiry)
        if serial:
            await page.get_by_label("الرقم التسلسلي للوحدة", exact=True).fill(serial)
        await page.get_by_label("سبب الإضافة", exact=True).fill("استلام تجريبي")
        await page.get_by_role("button", name="اعتماد الاستلام", exact=True).click()
        await expect(page.get_by_role("heading", name="إضافة مخزون", exact=True)).to_be_visible()

    async def positions(self, page, query):
        await page.goto(self.live_server_url + "/inventory/positions/?q=" + query)
        return page.get_by_role("table", name="أرصدة التتبع").locator("tbody tr")

    async def reverse(self, page):
        await page.get_by_text("عكس العملية", exact=True).click()
        await page.get_by_label("سبب العكس", exact=True).fill("عكس تجريبي")
        await page.get_by_role("button", name="اعتماد العكس", exact=True).click()
        await expect(page.get_by_role("heading", name="عكس عملية مخزون", exact=True)).to_be_visible()

    async def test_lot_receive_reserve_issue_transfer_count_and_reversals(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.login(page)
            await page.locator('a[href="/inventory/"]').first.click()
            await expect(page.get_by_role("heading", name="المخزون", exact=True)).to_be_visible()
            await page.get_by_role("link", name="استلام مخزون", exact=True).click()
            await page.get_by_label("بحث الاسم أو SKU أو الباركود", exact=True).fill(self.skus["contact_lens"])
            await page.get_by_role("button", name="بحث", exact=True).click()
            await page.locator("tbody tr").filter(has_text=self.skus["contact_lens"]).get_by_role("link", name="استلام", exact=True).click()
            await self.receive(page, "contact_lens", 5, lot="LOT-UI")
            await expect(page.get_by_text("LOT-UI", exact=True)).to_be_visible()
            rows = await self.positions(page, "LOT-UI")
            await rows.get_by_role("link", name="حجز", exact=True).click()
            await page.get_by_label("الكمية المحجوزة", exact=True).fill("2")
            await page.get_by_label("سبب الحجز", exact=True).fill("حجز دفعة تجريبي")
            await page.get_by_role("button", name="اعتماد الحجز", exact=True).click()
            await expect(page.get_by_text("LOT-UI", exact=True)).to_be_visible()
            await page.get_by_label("الكمية", exact=True).fill("1")
            await page.get_by_label("السبب", exact=True).fill("صرف من الدفعة")
            await page.get_by_role("button", name="صرف الكمية", exact=True).click()
            await page.get_by_label("السبب", exact=True).fill("تحرير المتبقي")
            await page.get_by_role("button", name="إلغاء كل المتبقي", exact=True).click()
            rows = await self.positions(page, "LOT-UI")
            await rows.get_by_role("link", name="تحويل", exact=True).click()
            await page.get_by_label("الكمية المحولة", exact=True).fill("2")
            await page.get_by_label("الفرع الوجهة", exact=True).select_option(self.other_id)
            await page.get_by_label("سبب العملية", exact=True).fill("نقل الدفعة للمستودع")
            await page.get_by_role("button", name="اعتماد العملية", exact=True).click()
            await expect(page.get_by_role("heading", name="تحويل مخزون", exact=True)).to_be_visible()
            transfer_url = page.url
            rows = await self.positions(page, "LOT-UI")
            await rows.filter(has_text=self.other_name).get_by_role("link", name="جرد", exact=True).click()
            await page.get_by_label("الكمية الفعلية المعدودة", exact=True).fill("1")
            await page.get_by_label("سبب العملية", exact=True).fill("جرد الدفعة")
            await page.get_by_role("button", name="اعتماد العملية", exact=True).click()
            await expect(page.get_by_role("heading", name="جرد مخزون", exact=True)).to_be_visible()
            await self.reverse(page)
            await page.goto(transfer_url)
            await self.reverse(page)
            await self.positions(page, "LOT-UI")
            await page.screenshot(path=str(ARTIFACTS / "tracking-lot-desktop.png"), full_page=True)
            await page.goto(self.live_server_url + "/inventory/trace/?q=LOT-UI")
            await expect(page.get_by_role("heading", name="سجل حركات المخزون", exact=True)).to_be_visible()
            await expect(page.get_by_text("LOT-UI", exact=True).first).to_be_visible()
            await browser.close()

    async def test_mobile_nojs_frame_expiry_serial_and_branch_history(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.login(page)
            await self.receive(page, "frame", 3)
            await page.goto(self.live_server_url + "/inventory/reservations/")
            await page.get_by_label("الصنف والفرع", exact=True).select_option(index=1)
            await page.get_by_label("الكمية", exact=True).fill("1")
            await page.get_by_label("سبب الحجز", exact=True).fill("حجز إطار")
            await page.get_by_role("button", name="اعتماد الحجز", exact=True).click()
            await page.get_by_label("الكمية", exact=True).fill("1")
            await page.get_by_label("السبب", exact=True).fill("صرف إطار")
            await page.get_by_role("button", name="صرف الكمية", exact=True).click()
            rows = await self.positions(page, "OLD-BATCH")
            await expect(rows.get_by_text("منتهية", exact=True)).to_be_visible()
            await expect(rows.get_by_role("link", name="حجز", exact=True)).to_have_count(0)
            await self.receive(page, "device", 1, serial=self.serial)
            rows = await self.positions(page, self.serial)
            await rows.get_by_role("link", name="حجز", exact=True).click()
            position_url = page.url
            await page.get_by_label("الكمية المحجوزة", exact=True).fill("1")
            await page.get_by_label("سبب الحجز", exact=True).fill("حجز الجهاز")
            await page.get_by_role("button", name="اعتماد الحجز", exact=True).click()
            await page.get_by_label("الكمية", exact=True).fill("1")
            await page.get_by_label("السبب", exact=True).fill("صرف الوحدة")
            await page.get_by_role("button", name="صرف الكمية", exact=True).click()
            await page.get_by_text("عكس الصرف", exact=True).click()
            await page.get_by_label("سبب العكس", exact=True).fill("استرجاع الوحدة")
            await page.get_by_role("button", name="اعتماد عكس الصرف", exact=True).click()
            rows = await self.positions(page, self.serial)
            await rows.get_by_role("link", name="تحويل", exact=True).click()
            await page.get_by_label("الكمية المحولة", exact=True).fill("1")
            await page.get_by_label("الفرع الوجهة", exact=True).select_option(self.other_id)
            await page.get_by_label("سبب العملية", exact=True).fill("نقل الجهاز")
            await page.get_by_role("button", name="اعتماد العملية", exact=True).click()
            await expect(page.get_by_text(self.serial, exact=True)).to_be_visible()
            self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            await page.screenshot(path=str(ARTIFACTS / "tracking-serial-mobile-nojs.png"), full_page=True)
            await context.close()
            context = await browser.new_context()
            page = await context.new_page()
            await self.login(page, "clerk")
            response = await page.goto(position_url)
            self.assertEqual(response.status, 404)
            await page.goto(self.live_server_url + "/inventory/trace/?q=" + self.serial)
            await expect(page.get_by_text(self.other_name, exact=True)).to_have_count(0)
            await expect(page.get_by_text(self.serial, exact=True).first).to_be_visible()
            await browser.close()
