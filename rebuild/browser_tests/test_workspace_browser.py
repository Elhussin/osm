import os
import uuid
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from playwright.async_api import async_playwright, expect
from directory.provisioning import provision_company
from django.contrib.auth import get_user_model
from access.models import Branch
from access.services import create_member, assign_role
from django_tenants.utils import tenant_context

PASSWORD = "Synthetic-Browser-2026!"
ARTIFACTS = Path(__file__).resolve().parents[1] / ".tools" / "ui-artifacts"


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"], SECURE_SSL_REDIRECT=False, DEBUG=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"], INVITE_DELIVERY="smtp",
                   EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAIL_HOST="smtp.example.invalid", DEFAULT_FROM_EMAIL="noreply@example.invalid")
class WorkspaceBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        self.company = provision_company(name="شركة البصريات التجريبية", domain="localhost", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        with tenant_context(self.company):
            owner = get_user_model().objects.get(username="owner")
            self.branch_id = str(Branch.objects.get(code="MAIN").pk)
            for name in ("sara", "ahmed", "nour"):
                member = create_member(owner.pk, username=name, password=PASSWORD, email=f"{name}@example.invalid")
                assign_role(owner.pk, user_id=member.pk, role_code="cashier", branch_id=self.branch_id)
        ARTIFACTS.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    async def sign_in(self, page, username="owner"):
        page.set_default_timeout(10000)
        response = await page.goto(self.live_server_url + "/auth/login/")
        self.assertEqual(response.status, 200)
        await page.screenshot(path=str(ARTIFACTS / "login.png"), full_page=True)
        await page.get_by_label("اسم المستخدم", exact=True).fill(username)
        await page.get_by_label("كلمة المرور", exact=True).fill(PASSWORD)
        login_responses = []
        page.on("response", lambda r: login_responses.append(r.status) if urlsplit(r.url).path == "/auth/login/" else None)
        await page.get_by_role("button", name="تسجيل الدخول", exact=True).click()
        try:
            await page.wait_for_url("**/account/")
        except Exception:
            await page.screenshot(path=str(ARTIFACTS / "login-after-submit.png"), full_page=True)
            raise AssertionError(f"Login navigation failed; HTTP statuses: {login_responses}") from None

    async def test_desktop_htmx_search_and_keyboard_navigation(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await context.new_page()
            external = []
            page.on("request", lambda request: external.append(request.url) if urlsplit(request.url).hostname not in {"localhost", "127.0.0.1"} else None)
            await self.sign_in(page)
            await page.screenshot(path=str(ARTIFACTS / "desktop-overview.png"), full_page=True)
            await page.wait_for_function("window.htmx !== undefined")
            await page.evaluate("window.__workspaceMarker = 'preserved'")
            await page.locator(".sidebar").get_by_role("link", name="الأعضاء", exact=True).click()
            await page.wait_for_url("**/account/members/")
            await expect(page.get_by_role("heading", name="الأعضاء", exact=True)).to_be_visible()
            self.assertEqual(await page.evaluate("window.__workspaceMarker"), "preserved")
            await page.get_by_label("البحث عن عضو", exact=True).fill("not-found")
            await page.get_by_role("button", name="بحث", exact=True).click()
            await expect(page.get_by_role("heading", name="لا توجد نتائج مطابقة")).to_be_visible()
            await page.get_by_label("البحث عن عضو", exact=True).fill("")
            await page.get_by_role("button", name="بحث", exact=True).click()
            await expect(page.get_by_role("link", name="إدارة sara", exact=True)).to_be_visible()
            await page.screenshot(path=str(ARTIFACTS / "desktop-members.png"), full_page=True)
            self.assertFalse(external, "The application must not request external assets")
            self.assertEqual(await page.locator("html").get_attribute("dir"), "rtl")
            await browser.close()

    async def test_invite_email_acceptance_and_limited_user(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await self.sign_in(page)
            await page.get_by_role("link", name="دعوة عضو", exact=True).click()
            await page.get_by_label("اسم المستخدم", exact=True).fill("browser-member")
            await page.get_by_label("البريد الإلكتروني", exact=True).fill("synthetic@example.invalid")
            await page.get_by_label("الدور", exact=True).select_option("cashier")
            await page.get_by_label("الفرع", exact=True).select_option(self.branch_id)
            await page.get_by_role("button", name="إنشاء الدعوة", exact=True).click()
            await expect(page.get_by_role("heading", name="الدعوة جاهزة")).to_be_visible()
            await expect(page.get_by_text("أُضيفت الرسالة إلى قائمة الإرسال", exact=False)).to_be_visible()
            private_url = await page.locator("#private-link").input_value()
            invited_context = await browser.new_context()
            invitee = await invited_context.new_page()
            try:
                await invitee.goto(private_url)
                await invitee.wait_for_function("location.hash === ''")
                await invitee.get_by_label("كلمة المرور الجديدة", exact=True).fill(PASSWORD)
                await invitee.get_by_label("تأكيد كلمة المرور", exact=True).fill(PASSWORD)
                await invitee.get_by_role("button", name="حفظ كلمة المرور", exact=True).click()
                await invitee.wait_for_url("**/auth/login/")
            except Exception:
                raise AssertionError("Invitation acceptance failed; private link and token redacted") from None
            await self.sign_in(invitee, username="browser-member")
            self.assertEqual(await invitee.get_by_role("link", name="الأعضاء", exact=True).count(), 0)
            response = await invitee.goto(self.live_server_url + "/account/members/")
            self.assertEqual(response.status, 403)
            await expect(invitee.get_by_role("heading", name="لا تملك صلاحية لهذا الإجراء")).to_be_visible()
            await browser.close()

    async def test_mobile_dialog_tablet_width_and_focus(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
            page = await context.new_page()
            await self.sign_in(page)
            button = page.get_by_role("button", name="فتح القائمة", exact=True)
            await button.focus()
            await page.keyboard.press("Enter")
            await expect(page.locator("#mobile-menu")).to_be_visible()
            await page.keyboard.press("Escape")
            await expect(page.locator("#mobile-menu")).not_to_be_visible()
            await expect(button).to_be_focused()
            await button.click()
            await page.locator("#mobile-menu").get_by_role("link", name="الأعضاء", exact=True).click()
            await page.wait_for_url("**/account/members/")
            await expect(page.get_by_role("heading", name="الأعضاء", exact=True)).to_be_visible()
            self.assertEqual(await page.evaluate("innerWidth"), 390)
            self.assertEqual(await page.evaluate("document.documentElement.getBoundingClientRect().x"), 0)
            await page.screenshot(path=str(ARTIFACTS / "mobile-members.png"), full_page=True)
            for width in (390, 768, 1440):
                await page.set_viewport_size({"width": width, "height": 900})
                self.assertTrue(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Page overflow at {width}px")
            await page.get_by_role("link", name="تخطي إلى المحتوى", exact=True).focus()
            await page.keyboard.press("Enter")
            await expect(page.locator("#main-content")).to_be_focused()
            await browser.close()

    async def test_no_javascript_forms_and_validation(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(java_script_enabled=False, viewport={"width": 1280, "height": 900})
            page = await context.new_page()
            await self.sign_in(page)
            await page.locator(".sidebar").get_by_role("link", name="الفروع والمستودعات", exact=True).click()
            await page.get_by_role("link", name="إضافة فرع", exact=True).click()
            await page.get_by_label("اسم الفرع", exact=True).fill("فرع الاختبار")
            await page.get_by_label("رمز الفرع", exact=True).fill("MAIN")
            await page.get_by_role("button", name="حفظ الفرع", exact=True).click()
            await expect(page.get_by_role("alert")).to_be_visible()
            self.assertEqual(await page.get_by_label("اسم الفرع", exact=True).input_value(), "فرع الاختبار")
            await page.get_by_label("رمز الفرع", exact=True).fill("BR03")
            await page.get_by_role("button", name="حفظ الفرع", exact=True).click()
            await page.wait_for_url("**/account/branches/")
            await expect(page.get_by_text("فرع الاختبار", exact=True)).to_be_visible()
            await browser.close()
