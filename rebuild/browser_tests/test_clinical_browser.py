from io import BytesIO
from pathlib import Path
import uuid
from PIL import Image, ImageDraw
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from django_tenants.utils import tenant_context
from playwright.async_api import async_playwright, expect
from directory.provisioning import provision_company
from access.models import Branch
from access.services import create_member, assign_role
from clinical.services import create_customer, record_prescription

PASSWORD = "Synthetic-Clinical-Browser-2026!"
ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ClinicalBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        company = provision_company(name="شركة البصريات التجريبية", domain="localhost", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        buffer = BytesIO()
        image = Image.new("RGB", (700, 360), "white")
        draw = ImageDraw.Draw(image)
        draw.text((30, 25), "SYNTHETIC EYE EXAM - TEST DATA ONLY", fill="black")
        draw.text((30, 70), "OD: SPH 0.00 / CYL -1.25 / AXIS 90", fill="black")
        image.save(buffer, "PNG")
        self.image_bytes = buffer.getvalue()
        with tenant_context(company):
            owner = get_user_model().objects.get(username="owner")
            self.branch_id = str(Branch.objects.get(code="MAIN").pk)
            customer = create_customer(owner.pk, branch_id=self.branch_id, first_name="عميل", last_name="تجريبي", phone="0501234567")
            self.customer_id = str(customer.pk)
            cashier = create_member(owner.pk, username="cashier", password=PASSWORD)
            assign_role(owner.pk, user_id=cashier.pk, role_code="cashier", branch_id=self.branch_id)
            revision = record_prescription(owner.pk, customer_id=customer.pk, branch_id=self.branch_id, source="external", examined_on=timezone.localdate(), right_sphere=0, image=SimpleUploadedFile("synthetic.png", self.image_bytes, content_type="image/png"))
            self.document_id = str(revision.prescription_id)
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

    async def test_customer_exam_image_correction_and_history(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 1000})
            await self.login(page)
            await page.locator(".sidebar").get_by_role("link", name="العملاء والفحوص", exact=True).click()
            await page.get_by_role("link", name="إضافة عميل", exact=True).click()
            await page.get_by_label("الاسم الأول", exact=True).fill("سارة")
            await page.get_by_label("اسم العائلة", exact=True).fill("التجريبية")
            await page.get_by_label("رقم الهاتف", exact=True).fill("٠٥٠١٢٣٤٥٦٧")
            await page.get_by_label("الفرع", exact=True).select_option(self.branch_id)
            await page.get_by_role("button", name="حفظ العميل", exact=True).click()
            await expect(page.get_by_role("heading", name="سارة التجريبية", exact=True)).to_be_visible()
            customer_url = page.url
            await page.get_by_role("link", name="تسجيل فحص ووصفة", exact=True).click()
            await page.get_by_label("SPH اليمنى", exact=True).fill("0")
            await page.get_by_label("CYL اليمنى", exact=True).fill("-1.25")
            await page.get_by_label("AXIS اليمنى", exact=True).fill("181")
            await page.locator("form.clinical-form").evaluate("f => f.noValidate = true")
            await page.get_by_role("button", name="حفظ الفحص والوصفة", exact=True).click()
            await expect(page.locator("#id_right_axis")).to_have_value("181")
            await expect(page.locator("#id_right_sphere")).to_have_value("0")
            await expect(page.locator(".field-invalid")).to_be_visible()
            await page.get_by_label("AXIS اليمنى", exact=True).fill("90")
            await page.get_by_label("صورة فحص النظر (اختيارية)", exact=True).set_input_files({"name": "synthetic.png", "mimeType": "image/png", "buffer": self.image_bytes})
            await page.get_by_role("button", name="حفظ الفحص والوصفة", exact=True).click()
            await page.wait_for_url("**/v/1/")
            original_url = page.url
            await page.get_by_text("عرض صورة الفحص", exact=True).click()
            await expect(page.get_by_role("img", name="صورة فحص النظر المرفقة بهذا الإصدار")).to_be_visible()
            await page.wait_for_function("document.querySelector('img.exam-image')?.complete && document.querySelector('img.exam-image').naturalWidth > 0")
            await expect(page.locator(".prescription-table tbody tr").first.locator("td").nth(1)).to_have_text("—")
            await page.screenshot(path=str(ARTIFACTS / "clinical-exam-desktop.png"), full_page=True)
            await page.get_by_role("link", name="تصحيح بإصدار جديد", exact=True).click()
            await page.get_by_label("SPH اليمنى", exact=True).fill("1.00")
            await page.get_by_label("سبب التصحيح", exact=True).fill("تصحيح تجريبي مع حفظ التاريخ")
            await page.get_by_role("button", name="حفظ إصدار مصحح", exact=True).click()
            await page.wait_for_url("**/v/2/")
            await expect(page.locator(".prescription-table tbody tr").first.locator("td").first).to_have_text("1.00")
            await page.goto(original_url)
            await expect(page.locator(".prescription-table tbody tr").first.locator("td").first).to_have_text("0.00")
            await expect(page.get_by_text("هذا إصدار سابق محفوظ للتاريخ.", exact=False)).to_be_visible()
            await page.goto(customer_url)
            await expect(page.get_by_role("link", name="عرض فحص الإصدار 2", exact=True)).to_be_visible()
            await page.goto(self.live_server_url + "/customers/")
            await page.get_by_label("البحث عن عميل", exact=True).fill("غيرموجود")
            await page.get_by_role("button", name="بحث", exact=True).click()
            await expect(page.get_by_role("heading", name="لا توجد نتائج مطابقة")).to_be_visible()
            await page.get_by_label("البحث عن عميل", exact=True).fill("سارة")
            await page.get_by_role("button", name="بحث", exact=True).click()
            await expect(page.get_by_role("link", name="ملف سارة التجريبية", exact=True)).to_be_visible()
            await browser.close()

    async def test_mobile_no_javascript_exam_without_image_and_edit_customer(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 390, "height": 844}, java_script_enabled=False, is_mobile=True, has_touch=True)
            await self.login(page)
            await page.goto(self.live_server_url + f"/customers/{self.customer_id}/")
            await page.get_by_role("link", name="تعديل البيانات", exact=True).click()
            await page.get_by_label("اسم العائلة", exact=True).fill("توثيق تجريبي")
            await page.get_by_role("button", name="حفظ العميل", exact=True).click()
            await page.get_by_role("link", name="تسجيل فحص ووصفة", exact=True).click()
            for width in (390, 768, 1440):
                await page.set_viewport_size({"width": width, "height": 950})
                self.assertEqual(await page.evaluate("innerWidth"), width)
                self.assertEqual(await page.evaluate("document.documentElement.getBoundingClientRect().x"), 0)
                self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.get_by_label("SPH اليمنى", exact=True).fill("0")
            await page.evaluate("window.scrollTo(0, 0)")
            await page.screenshot(path=str(ARTIFACTS / "clinical-exam-form-mobile.png"), full_page=True)
            await page.get_by_role("button", name="حفظ الفحص والوصفة", exact=True).click()
            await page.wait_for_url("**/v/1/")
            await expect(page.get_by_text("لم تُرفق صورة بهذا الإصدار. إرفاق الصورة اختياري.")).to_be_visible()
            await page.screenshot(path=str(ARTIFACTS / "clinical-exam-mobile.png"), full_page=True)
            await browser.close()

    async def test_cashier_can_read_customer_but_not_clinical_image(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await self.login(page, "cashier")
            await page.goto(self.live_server_url + f"/customers/{self.customer_id}/")
            self.assertEqual(await page.get_by_role("link", name="تسجيل فحص ووصفة", exact=True).count(), 0)
            self.assertEqual(await page.get_by_role("link", name="عرض فحص الإصدار 1", exact=True).count(), 0)
            response = await page.goto(self.live_server_url + f"/prescriptions/{self.document_id}/v/1/image/")
            self.assertEqual(response.status, 404)
            await browser.close()
