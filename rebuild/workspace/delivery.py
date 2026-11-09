from urllib.parse import urlencode
from django.conf import settings
from django.core import signing
from django.urls import reverse
from django.utils import timezone
from access.services import audit
from identity.models import LinkDelivery


def link_url(request, token, purpose):
    return request.build_absolute_uri(reverse("password-link", args=[purpose])) + "#" + urlencode({"token": token})


def deliver_link(request, *, user, token, purpose, actor_id):
    url = link_url(request, token, purpose)
    if settings.INVITE_DELIVERY != "smtp":
        return {"delivery": "manual", "private_url": url, "private_token": token}
    data = signing.loads(token, salt="erp.password-link", max_age=3600)
    _, created = LinkDelivery.objects.get_or_create(link_id=data["link"], defaults={
        "url_base": url.split("#", 1)[0], "recipient": user.email, "company_name": request.company.name,
        "actor_id": actor_id, "available_at": timezone.now(),
    })
    if created:
        audit(actor_id, "invitation.email_queued", user.pk)
    return {"delivery": "queued", "private_url": url, "private_token": token}
