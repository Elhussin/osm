from pathlib import Path
from io import BytesIO
import uuid
from PIL import Image
import zxingcpp
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from access.models import Branch
from access.services import create_member, assign_role, create_branch
from directory.provisioning import provision_company
from catalog.services import create_product, create_variant
from inventory.services import receive_matrix

PASSWORD = "Synthetic-Inventory-Browser-2026!"
ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class InventoryBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        company = provision_company(name="شركة البصريات التجريبية", domain="localhost", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        with tenant_context(company):
            owner = get_user_model().objects.get(username="owner")
            self.branch_id = str(Branch.objects.get(code="MAIN").pk)
            other = create_branch(owner.pk, code="SECOND", name="الفرع الآخر التجريبي")
            self.other_id = str(other.pk)
            for username, role in (("clerk", "inventory_clerk"), ("reader", "catalog_reader")):
                member = create_member(owner.pk, username=username, password=PASSWORD)
                assign_role(owner.pk, user_id=member.pk, role_code=role, branch_id=self.branch_id if role == "inventory_clerk" else None)
                if role == "inventory_clerk":
                    assign_role(owner.pk, user_id=member.pk, role_code="catalog_reader")
            product = create_product(owner.pk, code_value="LENS-MATRIX", name="عدسات مخزنية تجريبية", kind="stock_lens", brand="Synthetic")
            self.product_id = str(product.pk)
            specs = {"material": "Resin", "index": "1.60", "diameter": "70", "design": "single", "coatings": "AR, UV", "sphere": "0", "cylinder": "0"}
            template = create_variant(owner.pk, product_id=product.pk, sku="LENS-0", unit="piece", base_price="20.00", specifications=specs)
            self.template_id = str(template.pk)
            create_variant(owner.pk, product_id=product.pk, sku="LENS-025", unit="piece", base_price="22.00", specifications={**specs, "sphere": "0.25"})
            self.other_family = str(create_variant(owner.pk, product_id=product.pk, sku="LENS-UV", unit="piece", base_price="20.00", specifications={**specs, "coatings": "UV"}).pk)
            self.pair_family = str(create_variant(owner.pk, product_id=product.pk, sku="LENS-PAIR", unit="pair", base_price="35.00", specifications=specs).pk)
            self.other_receipt = str(receive_matrix(owner.pk, product_id=product.pk, template_id=template.pk, template_version=1, branch_id=other.pk, operation_key=uuid.uuid4(), reason="Synthetic other branch", cells=[{"sphere": "0", "cylinder": "0", "quantity": 9}]).pk)
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

    def matrix_url(self, template=None, wide=False):
        return self.live_server_url + f"/inventory/lenses/{self.product_id}/?branch_id={self.branch_id}&template_id={template or self.template_id}&sphere_min=0&sphere_max=0.25&cylinder_min={'-2' if wide else '-0.25'}&cylinder_max=0"

    async def paste(self, page, value):
        await page.evaluate("value => navigator.clipboard.writeText(value)", value)
        await page.locator('[name="q_0_0"]').focus()
        await page.keyboard.press("Control+V")

    async def label_layout_ready(self, page):
        await page.wait_for_load_state("load")
        await expect(page.locator('link[rel="stylesheet"]')).to_have_count(2)
        await page.wait_for_function("Array.from(document.querySelectorAll('link[rel=stylesheet]')).every(link => link.sheet !== null)")
        await page.evaluate("document.fonts.ready")

    async def test_desktop_excel_paste_preview_edit_commit_grouping_and_reverse(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000}, permissions=["clipboard-read", "clipboard-write"])
            page = await context.new_page()
            await self.login(page)
            await page.goto(self.matrix_url())
            await self.paste(page, "1\t2\n3\t4")
            for name, value in (("q_0_0", "1"), ("q_0_1", "2"), ("q_1_0", "3"), ("q_1_1", "4")):
                await expect(page.locator(f'[name="{name}"]')).to_have_value(value)
            await page.keyboard.press("ArrowRight")
            await expect(page.locator('[name="q_0_1"]')).to_be_focused()
            await self.paste(page, "9\t-1")
            await expect(page.locator("#matrix-paste-feedback")).to_be_visible()
            await expect(page.locator('[name="q_0_0"]')).to_have_value("1")
            await self.paste(page, "1\t2\n3\t4")
            await page.get_by_label("سبب الإضافة", exact=True).fill("رصيد افتتاحي تجريبي")
            await page.get_by_label("المتغيرات الناقصة", exact=True).select_option("yes")
            await page.get_by_role("button", name="معاينة الإضافة", exact=True).click()
            await expect(page.get_by_role("heading", name="مراجعة إضافة المخزون", exact=True)).to_be_visible()
            await expect(page.get_by_text("الإضافة: 10", exact=False)).to_be_visible()
            await page.get_by_role("button", name="الرجوع لتعديل الكميات", exact=True).click()
            await expect(page.locator('[name="q_1_1"]')).to_have_value("4")
            await page.get_by_role("button", name="معاينة الإضافة", exact=True).click()
            await page.get_by_role("button", name="اعتماد إضافة المخزون", exact=True).click()
            await page.wait_for_url("**/inventory/receipts/*/")
            receipt_url = page.url
            await expect(page.get_by_role("heading", name="إضافة مخزون", exact=True)).to_be_visible()
            await page.goto(self.matrix_url())
            await expect(page.locator('[data-balance-name="q_1_1"]')).to_have_text("4")
            await page.screenshot(path=str(ARTIFACTS / "lens-matrix-desktop.png"), full_page=True)
            for template in (self.other_family, self.pair_family):
                await page.goto(self.matrix_url(template))
                await expect(page.locator('[data-balance-name="q_1_0"]')).to_have_text("0")
            await page.goto(receipt_url)
            await page.get_by_text("عكس إضافة المخزون", exact=True).click()
            await page.get_by_label("سبب العكس", exact=True).fill("تصحيح تجريبي")
            await page.get_by_role("button", name="اعتماد العكس", exact=True).click()
            await expect(page.get_by_role("heading", name="عكس إضافة", exact=True)).to_be_visible()
            await page.goto(self.matrix_url())
            await expect(page.locator('[data-balance-name="q_1_1"]')).to_have_text("0")
            await browser.close()

    async def test_reservation_issue_cancel_inverse_and_mobile_without_javascript(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.login(page)
            await page.goto(self.live_server_url + "/inventory/reservations/")
            # The owner can reserve the synthetic receipt in the second branch.
            await page.get_by_label("الصنف والفرع", exact=True).select_option(index=1)
            await page.get_by_label("الكمية", exact=True).fill("5")
            await page.get_by_label("سبب الحجز", exact=True).fill("حجز تجريبي")
            await page.get_by_role("button", name="اعتماد الحجز", exact=True).click()
            await expect(page.get_by_role("heading", name="تفاصيل الحجز", exact=True)).to_be_visible()
            await page.get_by_label("السبب", exact=True).fill("صرف تجريبي")
            await page.get_by_label("الكمية", exact=True).fill("2")
            await page.get_by_role("button", name="صرف الكمية", exact=True).click()
            await expect(page.get_by_text("الأصل: 5 · المتبقي: 3 · المصروف: 2 · المحرر: 0", exact=True)).to_be_visible()
            await page.get_by_label("السبب", exact=True).fill("إلغاء المتبقي تجريبيًا")
            await page.get_by_role("button", name="إلغاء كل المتبقي", exact=True).click()
            await expect(page.get_by_text("أُلغي المتبقي من الحجز.", exact=True)).to_be_visible()
            await page.get_by_text("عكس الصرف", exact=True).click()
            await page.get_by_label("سبب العكس", exact=True).fill("عكس تجريبي")
            await page.get_by_role("button", name="اعتماد عكس الصرف", exact=True).click()
            await expect(page.get_by_text("الأصل: 5 · المتبقي: 0 · المصروف: 0 · المحرر: 5", exact=True)).to_be_visible()
            await page.screenshot(path=str(ARTIFACTS / "reservation-mobile-nojs.png"), full_page=True)
            self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            detail = page.url
            await context.close()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            await self.login(page, "clerk")
            response = await page.goto(detail)
            self.assertEqual(response.status, 404)
            await page.goto(self.live_server_url + "/inventory/reservations/")
            await expect(page.get_by_text("لا توجد حجوزات.", exact=True)).to_be_visible()
            await browser.close()

    async def test_desktop_reservation_named_commands_and_matrix_available(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            await self.login(page)
            await page.goto(self.live_server_url + "/inventory/reservations/")
            await page.get_by_label("الصنف والفرع", exact=True).select_option(index=1)
            await page.get_by_label("الكمية", exact=True).fill("3")
            await page.get_by_label("سبب الحجز", exact=True).fill("حجز سطح المكتب")
            await page.get_by_role("button", name="اعتماد الحجز", exact=True).click()
            await expect(page.get_by_role("heading", name="تفاصيل الحجز", exact=True)).to_be_visible()
            detail = page.url
            await page.goto(self.matrix_url().replace(self.branch_id, self.other_id))
            await expect(page.locator('[data-balance-name="q_1_0"]')).to_have_text("6")
            await page.goto(detail)
            await page.get_by_label("الكمية", exact=True).fill("1")
            await page.get_by_label("السبب", exact=True).fill("صرف جزئي")
            await page.get_by_role("button", name="صرف الكمية", exact=True).click()
            await expect(page.get_by_text("الأصل: 3 · المتبقي: 2 · المصروف: 1 · المحرر: 0", exact=True)).to_be_visible()
            await page.get_by_label("الكمية", exact=True).fill("1")
            await page.get_by_label("السبب", exact=True).fill("تحرير جزئي")
            await page.get_by_role("button", name="تحرير الكمية", exact=True).click()
            await expect(page.get_by_text("الأصل: 3 · المتبقي: 1 · المصروف: 1 · المحرر: 1", exact=True)).to_be_visible()
            await page.screenshot(path=str(ARTIFACTS / "reservation-desktop.png"), full_page=True)
            await browser.close()

    async def test_transfer_count_and_reversals_on_desktop(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.login(page)
            await page.goto(self.live_server_url + "/inventory/operations/")
            await page.get_by_role("link", name="تحويل", exact=True).click()
            await page.get_by_label("الفرع الوجهة", exact=True).select_option(self.branch_id)
            await page.get_by_label("الكمية المحولة", exact=True).fill("3")
            await page.get_by_label("سبب العملية", exact=True).fill("تحويل تجريبي")
            await page.get_by_role("button", name="اعتماد العملية", exact=True).click()
            await expect(page.get_by_role("heading", name="تحويل مخزون", exact=True)).to_be_visible()
            rows = page.get_by_role("table", name="حركات العملية").locator("tbody tr")
            await expect(rows).to_have_count(2)
            await page.get_by_text("عكس العملية", exact=True).click()
            await page.get_by_label("سبب العكس", exact=True).fill("عكس تحويل تجريبي")
            await page.get_by_role("button", name="اعتماد العكس", exact=True).click()
            await expect(page.get_by_role("heading", name="عكس عملية مخزون", exact=True)).to_be_visible()
            await page.goto(self.live_server_url + "/inventory/operations/")
            row = page.get_by_role("table", name="أرصدة التحويل والجرد").locator("tbody tr").filter(has_text="الفرع الآخر التجريبي")
            await row.get_by_role("link", name="جرد", exact=True).click()
            await page.get_by_label("الكمية الفعلية المعدودة", exact=True).fill("7")
            await page.get_by_label("سبب العملية", exact=True).fill("جرد تجريبي")
            await page.get_by_role("button", name="اعتماد العملية", exact=True).click()
            await expect(page.get_by_role("heading", name="جرد مخزون", exact=True)).to_be_visible()
            await expect(page.get_by_role("table", name="حركات العملية").locator("tbody tr")).to_have_count(1)
            await page.screenshot(path=str(ARTIFACTS / "stock-count-desktop.png"), full_page=True)
            await page.get_by_text("عكس العملية", exact=True).click()
            await page.get_by_label("سبب العكس", exact=True).fill("تصحيح الجرد التجريبي")
            await page.get_by_role("button", name="اعتماد العكس", exact=True).click()
            await expect(page.get_by_role("heading", name="عكس عملية مخزون", exact=True)).to_be_visible()
            await browser.close()

    async def test_mobile_nojs_zero_count_and_other_branch_denial(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.login(page)
            await page.goto(self.live_server_url + "/inventory/lenses/")
            await expect(page.get_by_role("link", name="التحويل والجرد", exact=True)).to_be_visible()
            await expect(page.get_by_role("link", name="حجوزات المخزون والصرف", exact=True)).to_be_visible()
            await page.goto(self.live_server_url + "/inventory/operations/")
            await page.get_by_role("link", name="جرد", exact=True).click()
            count_url = page.url
            await page.get_by_label("الكمية الفعلية المعدودة", exact=True).fill("0")
            await page.get_by_label("سبب العملية", exact=True).fill("جرد صفري تجريبي")
            await page.get_by_role("button", name="اعتماد العملية", exact=True).click()
            await expect(page.get_by_role("heading", name="جرد مخزون", exact=True)).to_be_visible()
            await expect(page.get_by_text("الكمية المسجلة: 0", exact=False)).to_be_visible()
            await page.screenshot(path=str(ARTIFACTS / "stock-count-mobile-nojs.png"), full_page=True)
            self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            document_url = page.url
            await context.close()
            context = await browser.new_context()
            page = await context.new_page()
            await self.login(page, "clerk")
            for url in (count_url, document_url):
                response = await page.goto(url)
                self.assertEqual(response.status, 404)
            await page.goto(self.live_server_url + "/inventory/operations/")
            await expect(page.get_by_text("لا توجد أرصدة مطابقة.", exact=True)).to_be_visible()
            await browser.close()

    async def test_barcode_labels_decode_print_media_and_pagination(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=3)
            page = await context.new_page()
            await self.login(page)
            await page.goto(self.live_server_url + f"/catalog/variants/{self.template_id}/")
            await page.get_by_role("link", name="ملصقات الباركود", exact=True).click()
            await page.get_by_label("عدد الملصقات", exact=True).fill("13")
            await page.get_by_role("button", name="معاينة الملصقات", exact=True).click()
            await expect(page.locator(".barcode-label")).to_have_count(13)
            await expect(page.locator(".label-sheet")).to_have_count(2)
            await self.label_layout_ready(page)
            image = await page.locator(".barcode-image").first.screenshot()
            decoded = zxingcpp.read_barcode(Image.open(BytesIO(image)))
            self.assertIsNotNone(decoded)
            self.assertEqual(decoded.text, "LENS-0")
            self.assertEqual(decoded.format, zxingcpp.BarcodeFormat.Code128)
            await page.evaluate("window.print = () => { window.__printRequested = true; }")
            await page.get_by_role("button", name="طباعة الملصقات", exact=True).click()
            self.assertTrue(await page.evaluate("window.__printRequested"))
            await page.emulate_media(media="print")
            await expect(page.locator(".print-tools")).to_be_hidden()
            geometry = await page.locator(".barcode-label").first.evaluate("el => ({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,image:el.querySelector('img').getBoundingClientRect().width,inside:el.clientWidth-parseFloat(getComputedStyle(el).paddingLeft)-parseFloat(getComputedStyle(el).paddingRight)})")
            self.assertAlmostEqual(geometry["width"], 90 * 96 / 25.4, delta=0.3)
            self.assertAlmostEqual(geometry["height"], 43 * 96 / 25.4, delta=0.3)
            self.assertLessEqual(geometry["image"], geometry["inside"] + 0.3)
            await page.locator(".label-sheet").first.screenshot(path=str(ARTIFACTS / "barcode-labels-print.png"))
            await page.emulate_media(media="screen")
            await page.goto(self.live_server_url + f"/catalog/variants/{self.template_id}/labels/")
            await page.get_by_label("عدد الملصقات", exact=True).fill("5")
            await page.get_by_label("قالب الطباعة", exact=True).select_option("wide")
            await page.get_by_role("button", name="معاينة الملصقات", exact=True).click()
            await expect(page.locator(".barcode-label")).to_have_count(5)
            await expect(page.locator(".label-sheet")).to_have_count(2)
            await self.label_layout_ready(page)
            await page.emulate_media(media="print")
            width = await page.locator(".barcode-label").first.evaluate("el => el.getBoundingClientRect().width")
            self.assertAlmostEqual(width, 270 * 96 / 25.4, delta=0.3)
            await page.locator(".label-sheet").first.screenshot(path=str(ARTIFACTS / "barcode-labels-wide-print.png"))
            await browser.close()

    async def test_barcode_labels_mobile_nojs_catalog_reader(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
            page = await context.new_page()
            await self.login(page, "reader")
            await page.goto(self.live_server_url + f"/catalog/variants/{self.template_id}/labels/")
            await page.get_by_label("عدد الملصقات", exact=True).fill("2")
            await page.get_by_role("button", name="معاينة الملصقات", exact=True).click()
            await expect(page.locator(".barcode-label")).to_have_count(2)
            await self.label_layout_ready(page)
            await expect(page.locator(".code-value").first).to_have_text("LENS-0")
            await expect(page.locator("#print-labels")).to_be_hidden()
            self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            await page.screenshot(path=str(ARTIFACTS / "barcode-labels-mobile-nojs.png"), full_page=True)
            await browser.close()

    async def test_mobile_no_javascript_existing_cells_only_and_scroll(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 390, "height": 844}, java_script_enabled=False, is_mobile=True, has_touch=True)
            await self.login(page, "clerk")
            await page.goto(self.matrix_url(wide=True))
            self.assertEqual(await page.locator('[name="q_0_1"]').count(), 0)
            for width in (390, 768, 1440):
                await page.set_viewport_size({"width": width, "height": 900})
                self.assertEqual(await page.evaluate("innerWidth"), width)
                self.assertEqual(await page.evaluate("document.documentElement.getBoundingClientRect().x"), 0)
                self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            await page.set_viewport_size({"width": 390, "height": 844})
            self.assertTrue(await page.locator(".matrix-scroll").evaluate("e => e.scrollWidth > e.clientWidth"))
            self.assertGreaterEqual((await page.locator(".matrix-corner").bounding_box())["width"], 90)
            await page.locator('[name="q_0_0"]').fill("2")
            await page.locator('[name="q_1_0"]').fill("3")
            await page.get_by_label("سبب الإضافة", exact=True).fill("إضافة تجريبية دون جافاسكربت")
            await page.evaluate("window.scrollTo(0,0)")
            await page.screenshot(path=str(ARTIFACTS / "lens-matrix-mobile.png"), full_page=True)
            await page.get_by_role("button", name="معاينة الإضافة", exact=True).click()
            await page.get_by_role("button", name="اعتماد إضافة المخزون", exact=True).click()
            await expect(page.get_by_role("heading", name="إضافة مخزون", exact=True)).to_be_visible()
            self.assertEqual(await page.get_by_role("button", name="اعتماد العكس", exact=True).count(), 0)
            await page.goto(self.matrix_url())
            await expect(page.locator('[data-balance-name="q_1_0"]')).to_have_text("3")
            await browser.close()

    async def test_other_branch_stock_and_catalog_only_reader_are_denied(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await self.login(page, "clerk")
            await page.goto(self.matrix_url())
            self.assertEqual(await page.locator('[name="branch_id"] option', has_text="الفرع الآخر التجريبي").count(), 0)
            response = await page.goto(self.live_server_url + f"/inventory/receipts/{self.other_receipt}/")
            self.assertEqual(response.status, 404)
            other = await browser.new_page()
            await self.login(other, "reader")
            response = await other.goto(self.live_server_url + "/inventory/lenses/")
            self.assertEqual(response.status, 403)
            await browser.close()
