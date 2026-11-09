"""Tenant-local outbox. Never hold a database transaction across SMTP."""
import smtplib
from datetime import timedelta
from urllib.parse import urlencode
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils import timezone
from access.services import audit
from identity.links import delivery_token
from identity.models import LinkDelivery


def process_pending(limit=20):
    if settings.INVITE_DELIVERY != "smtp":
        return 0
    processed = 0
    while processed < limit:
        with transaction.atomic():
            LinkDelivery.objects.filter(status="sending", attempts__gte=5, available_at__lte=timezone.now()).update(status="failed")
            job = LinkDelivery.objects.select_for_update(skip_locked=True).filter(
                status__in=["pending", "sending"], available_at__lte=timezone.now(), attempts__lt=5,
            ).select_related("link__user").order_by("available_at", "id").first()
            if job is None:
                break
            link, user = job.link, job.link.user
            if link.used_at or link.expires_at <= timezone.now() or not job.recipient or user.email != job.recipient or (link.purpose == "reset" and not user.is_active) or (link.purpose == "invite" and user.is_active):
                job.status = "cancelled"
                job.save(update_fields=["status"])
                processed += 1
                continue
            job.status = "sending"
            job.attempts += 1
            job.available_at = timezone.now() + timedelta(minutes=2)
            job.save(update_fields=["status", "attempts", "available_at"])
        # A stable Message-ID assists SMTP deduplication, but SMTP cannot promise exactly-once delivery.
        token = delivery_token(link)
        url = job.url_base + "#" + urlencode({"token": token})
        title = "دعوتك إلى " if link.purpose == "invite" else "استعادة حسابك في "
        body = f"مرحبًا،\n\nاستخدم الرابط التالي لتعيين كلمة مرور حسابك في {job.company_name}:\n{url}\n\nويمكنك إدخال الرمز يدويًا في صفحة تعيين كلمة المرور:\n{token}\n\nالرابط صالح لمدة ساعة من إصداره ويُستخدم مرة واحدة.\nإذا لم تكن تتوقع هذه الرسالة فتجاهلها."
        try:
            sent = EmailMessage(title + job.company_name, body, settings.DEFAULT_FROM_EMAIL, [job.recipient], headers={"Message-ID": f"<erp-link-{job.pk}@{job.url_base.split('/')[2]}>"}).send(fail_silently=False) == 1
        except (smtplib.SMTPException, OSError):
            sent = False
        with transaction.atomic():
            updated = LinkDelivery.objects.filter(pk=job.pk, status="sending", attempts=job.attempts).update(
                status="sent" if sent else ("failed" if job.attempts >= 5 else "pending"),
                sent_at=timezone.now() if sent else None,
                available_at=timezone.now() + timedelta(seconds=30 * 2 ** job.attempts),
            )
            if updated:
                audit(job.actor_id, "invitation.email_sent" if sent else "invitation.email_failed", user.pk)
        processed += 1
    return processed
