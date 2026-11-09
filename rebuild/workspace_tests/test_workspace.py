import re
import smtplib
import uuid
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from django.db import close_old_connections
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection
from django.test import Client, TransactionTestCase, override_settings
from django_tenants.utils import tenant_context
from directory.provisioning import provision_company
from access.models import Branch, RoleAssignment, AuditEvent
from access.services import create_member, assign_role
from identity.models import PasswordLink, LinkDelivery
from workspace.mail_worker import process_pending
from django.utils import timezone
from identity.invitations import invite_member
from identity.links import consume_link

PASSWORD = "Synthetic-Workspace-2026!"
SMTP = {"INVITE_DELIVERY": "smtp", "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend", "EMAIL_HOST": "smtp.example.invalid", "DEFAULT_FROM_EMAIL": "noreply@example.invalid"}


@override_settings(ALLOWED_HOSTS=["a.r05.test", "b.r05.test"], SECURE_SSL_REDIRECT=False, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class WorkspaceTests(TransactionTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        self.a = provision_company(name="Synthetic A", domain="a.r05.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        self.b = provision_company(name="Synthetic B", domain="b.r05.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        with tenant_context(self.a):
            self.owner = get_user_model().objects.get(username="owner")
            self.branch = Branch.objects.get(code="MAIN")
            self.cashier = create_member(self.owner.pk, username="cashier", password=PASSWORD)
            assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="cashier", branch_id=self.branch.pk)
        self.login()
        if hasattr(mail, "outbox"):
            mail.outbox.clear()

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def login(self, username="owner"):
        self.client = Client()
        self.assertEqual(self.client.post("/auth/login/", {"username": username, "password": PASSWORD}, HTTP_HOST="a.r05.test").status_code, 302)

    def get(self, path, data=None, **kwargs):
        return self.client.get(path, data, HTTP_HOST="a.r05.test", **kwargs)

    def post(self, path, data=None):
        return self.client.post(path, data or {}, HTTP_HOST="a.r05.test")

    def invite_data(self, username="new-member"):
        return {"username": username, "email": "synthetic@example.invalid", "role_code": "cashier", "branch_id": str(self.branch.pk)}

    @override_settings(**SMTP)
    def test_smtp_invite_pending_account_and_single_use_link(self):
        response = self.post("/account/members/invite/", self.invite_data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "أُضيفت الرسالة إلى قائمة الإرسال")
        self.assertEqual(len(getattr(mail, "outbox", [])), 0)
        with tenant_context(self.a):
            process_pending()
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue("http://a.r05.test/auth/link/invite/#token=" in mail.outbox[0].body, "Mail link mismatch; private content redacted")
        token = response.context["private_token"]
        with tenant_context(self.a):
            user = get_user_model().objects.get(username="new-member")
            self.assertFalse(user.is_active)
            self.assertFalse(token in str(list(AuditEvent.objects.values())), "Private token leaked into audit; value redacted")
        accepted = self.post("/auth/link/invite/", {"token": token, "password": PASSWORD, "password_confirmation": PASSWORD})
        self.assertEqual(accepted.status_code, 302)
        self.assertEqual(self.post("/auth/link/invite/", {"token": token, "password": PASSWORD, "password_confirmation": PASSWORD}).status_code, 400)

    @override_settings(**SMTP)
    def test_delivery_failure_preserves_account_and_retry_does_not_duplicate(self):
        response = self.post("/account/members/invite/", self.invite_data())
        user = response.context["member"]
        with tenant_context(self.a):
            with patch("workspace.mail_worker.EmailMessage.send", side_effect=smtplib.SMTPException("private-smtp-sentinel")):
                self.assertEqual(process_pending(), 1)
            job = LinkDelivery.objects.get()
            self.assertEqual(job.status, "pending")
            self.assertEqual(job.attempts, 1)
            LinkDelivery.objects.update(available_at=timezone.now())
            self.assertEqual(process_pending(), 1)
            self.assertEqual(process_pending(), 0)
            job.refresh_from_db()
            self.assertEqual(job.status, "sent")
            self.assertEqual(get_user_model().objects.filter(username="new-member").count(), 1)
            self.assertEqual(PasswordLink.objects.filter(user=user, used_at__isnull=True).count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_pending_invitation_cannot_be_activated_without_password(self):
        response = self.post("/account/members/invite/", self.invite_data())
        user = response.context["member"]
        result = self.post(f"/account/members/{user.pk}/state/", {"command": "activate"})
        self.assertEqual(result.status_code, 422)
        with tenant_context(self.a):
            self.assertFalse(get_user_model().objects.get(pk=user.pk).is_active)

    def test_privileged_pages_and_posts_are_denied_to_cashier(self):
        self.login("cashier")
        for path in ("/account/members/", "/account/roles/", "/account/ownership/", "/account/branches/new/"):
            self.assertEqual(self.get(path).status_code, 403)
        self.assertEqual(self.post("/account/members/invite/", self.invite_data()).status_code, 403)
        response = self.get("/account/")
        self.assertNotContains(response, "دعوة عضو")
        self.assertNotContains(response, 'href="/account/members/"')

    def test_admin_cannot_change_owner_email_or_select_more_powerful_role(self):
        with tenant_context(self.a):
            admin = create_member(self.owner.pk, username="admin", password=PASSWORD)
            assign_role(self.owner.pk, user_id=admin.pk, role_code="company_admin")
        self.login("admin")
        self.assertEqual(self.post(f"/account/members/{self.owner.pk}/", {"email": "attacker@example.invalid", "first_name": "", "last_name": ""}).status_code, 403)
        self.assertEqual(self.post(f"/account/members/{admin.pk}/roles/", {"role_code": "accountant"}).status_code, 422)
        with tenant_context(self.a):
            self.owner.refresh_from_db()
            self.assertNotEqual(self.owner.email, "attacker@example.invalid")
            self.assertFalse(RoleAssignment.objects.filter(user=admin, role_id="accountant").exists())

    def test_foreign_member_and_branch_identifiers_do_not_cross_company(self):
        with tenant_context(self.b):
            foreign = get_user_model().objects.get(username="owner")
            branch = Branch.objects.get(code="MAIN")
        self.assertEqual(self.get(f"/account/members/{foreign.pk}/").status_code, 404)
        self.assertEqual(self.post(f"/account/members/{self.cashier.pk}/roles/", {"role_code": "cashier", "branch_id": str(branch.pk)}).status_code, 422)

    def test_member_search_pagination_and_htmx_preserve_html_and_privacy(self):
        with tenant_context(self.a):
            get_user_model().objects.bulk_create([get_user_model()(username=f"synthetic-{i:02d}", password="!") for i in range(25)])
        response = self.get("/account/members/", {"q": "synthetic-", "page": 2}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.context["page_obj"].paginator.count, 25)
        self.assertEqual(len(response.context["page_obj"]), 5)
        self.assertContains(response, 'id="listing"')
        self.assertContains(response, "q=synthetic-")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertContains(response, 'hx-history="false"')

    def test_branch_create_duplicate_validation_and_edit(self):
        data = {"name": "فرع جديد", "code": "br02", "kind": "store"}
        self.assertEqual(self.post("/account/branches/new/", data).status_code, 302)
        duplicate = self.post("/account/branches/new/", data)
        self.assertEqual(duplicate.status_code, 422)
        self.assertContains(duplicate, "فرع جديد", status_code=422)
        with tenant_context(self.a):
            branch = Branch.objects.get(code="BR02")
        self.assertEqual(self.post(f"/account/branches/{branch.pk}/", {**data, "name": "اسم محدّث"}).status_code, 302)
        self.assertEqual(self.post(f"/account/branches/{branch.pk}/state/", {"command": "deactivate"}).status_code, 302)
        with tenant_context(self.a):
            branch.refresh_from_db()
            self.assertEqual(branch.name, "اسم محدّث")
            self.assertFalse(branch.active)

    @override_settings(**SMTP)
    def test_recovery_response_does_not_enumerate_accounts_or_expose_tokens(self):
        with tenant_context(self.a):
            self.cashier.email = "recipient@example.invalid"
            self.cashier.save(update_fields=["email"])
        self.client = Client()
        known = self.post("/auth/recovery/", {"username": "cashier"})
        unknown = self.post("/auth/recovery/", {"username": "no-such-account"})
        self.assertEqual(known.content, unknown.content)
        self.assertEqual(known.status_code, 200)
        with tenant_context(self.a):
            process_pending()
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(b"#token=", known.content)
        for _ in range(5):
            self.post("/auth/recovery/", {"username": "cashier"})
        with tenant_context(self.a):
            process_pending()
        self.assertEqual(len(mail.outbox), 2)  # superseded pending link is cancelled

    @override_settings(INVITE_DELIVERY="manual", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_unconfigured_mail_is_explicit_and_public_recovery_has_no_delivery(self):
        response = self.post("/account/members/invite/", self.invite_data())
        self.assertContains(response, "البريد الإلكتروني غير مهيأ")
        self.assertEqual(response.context["delivery"], "manual")
        self.client = Client()
        self.assertEqual(self.post("/auth/recovery/", {"username": "owner"}).status_code, 200)
        self.assertEqual(len(getattr(mail, "outbox", [])), 0)

    def test_password_confirmation_failure_does_not_consume_link(self):
        response = self.post("/account/members/invite/", self.invite_data())
        token = response.context["private_token"]
        invalid = self.post("/auth/link/invite/", {"token": token, "password": PASSWORD, "password_confirmation": "different"})
        self.assertEqual(invalid.status_code, 400)
        self.assertContains(invalid, "غير متطابقتين", status_code=400)
        with tenant_context(self.a):
            self.assertTrue(PasswordLink.objects.filter(user=response.context["member"], used_at__isnull=True).exists())

    def test_ownership_http_requires_password_and_updates_navigation(self):
        invalid = self.post("/account/ownership/", {"target": str(self.cashier.pk), "password": "wrong"})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(self.post("/account/ownership/", {"target": str(self.cashier.pk), "password": PASSWORD}).status_code, 302)
        self.assertEqual(self.get("/account/ownership/").status_code, 403)

    @override_settings(**SMTP)
    def test_mail_is_sent_outside_database_transaction(self):
        def send(*args, **kwargs):
            self.assertFalse(connection.in_atomic_block)
            return 1
        self.assertEqual(self.post("/account/members/invite/", self.invite_data()).status_code, 200)
        with tenant_context(self.a), patch("workspace.mail_worker.EmailMessage.send", side_effect=send):
            self.assertEqual(process_pending(), 1)

    @override_settings(**SMTP)
    def test_outbox_contains_no_bearer_secret_and_superseded_job_is_cancelled(self):
        response = self.post("/account/members/invite/", self.invite_data())
        user = response.context["member"]
        token = response.context["private_token"]
        with tenant_context(self.a):
            self.assertFalse(token in str(list(LinkDelivery.objects.values())), "Outbox must not retain a token")
        self.post(f"/account/members/{user.pk}/send/invite/")
        with tenant_context(self.a):
            self.assertEqual(process_pending(), 2)
            self.assertEqual(LinkDelivery.objects.filter(status="cancelled").count(), 1)
            self.assertEqual(LinkDelivery.objects.filter(status="sent").count(), 1)
            self.assertEqual(process_pending(), 0)
        self.assertEqual(len(mail.outbox), 1)
        sent_token = unquote(mail.outbox[0].body.split("#token=", 1)[1].splitlines()[0])
        with tenant_context(self.a):
            consume_link(sent_token, "invite", PASSWORD)

    @override_settings(**SMTP)
    def test_outbox_stops_after_five_failures_and_does_not_send_foreign_jobs(self):
        self.post("/account/members/invite/", self.invite_data())
        with tenant_context(self.b):
            self.assertEqual(process_pending(), 0)
        with tenant_context(self.a), patch("workspace.mail_worker.EmailMessage.send", side_effect=smtplib.SMTPException("redacted")):
            for _ in range(5):
                LinkDelivery.objects.update(available_at=timezone.now())
                self.assertEqual(process_pending(), 1)
            self.assertEqual(process_pending(), 0)
            self.assertEqual(LinkDelivery.objects.get().status, "failed")

    @override_settings(**SMTP)
    def test_two_workers_claim_one_job_without_holding_database_locks(self):
        self.post("/account/members/invite/", self.invite_data())
        sending, release = Event(), Event()

        def smtp(*args, **kwargs):
            sending.set()
            if not release.wait(10):
                raise AssertionError("Worker test timed out")
            return 1

        def worker():
            close_old_connections()
            try:
                with tenant_context(self.a):
                    return process_pending()
            finally:
                connection.close()

        with patch("workspace.mail_worker.EmailMessage.send", side_effect=smtp) as sender, ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(worker)
            try:
                self.assertTrue(sending.wait(10))
                with tenant_context(self.a):
                    self.assertEqual(process_pending(), 0)
            finally:
                release.set()
            self.assertEqual(future.result(timeout=10), 1)
            self.assertEqual(sender.call_count, 1)
