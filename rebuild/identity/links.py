import hashlib
import secrets
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from access.authorization import current_company, require, require_delegation
from access.services import audit, lock_access
from .models import PasswordLink


def delivery_token(link):
    """Reconstruct a queued token without retaining a bearer secret in the outbox."""
    company = current_company()
    nonce = salted_hmac("erp.password-link.nonce", f"{company.pk}:{link.pk}:{link.user_id}:{link.purpose}", algorithm="sha256").hexdigest()
    return signing.dumps({"link": str(link.pk), "company": str(company.pk), "user": str(link.user_id), "purpose": link.purpose, "nonce": nonce}, salt="erp.password-link", compress=False)


def _issue(user, purpose):
    PasswordLink.objects.filter(user=user, purpose=purpose, used_at__isnull=True).update(used_at=timezone.now())
    link = PasswordLink(user=user, purpose=purpose, expires_at=timezone.now() + timedelta(hours=1))
    token = delivery_token(link)
    nonce = signing.loads(token, salt="erp.password-link")["nonce"]
    link.digest = hashlib.sha256(nonce.encode()).hexdigest()
    link.save()
    return token


@transaction.atomic
def issue_link(actor_id, user_id, purpose):
    lock_access()
    require(actor_id, "members.manage")
    if purpose not in {"invite", "reset"}:
        raise PermissionDenied
    user = get_user_model().objects.get(pk=user_id)
    from access.models import RoleAssignment
    from access.policy import ROLES
    for assignment in RoleAssignment.objects.filter(user=user, active=True):
        require_delegation(actor_id, ROLES[assignment.role_id], assignment.branch_id)
    if (purpose == "invite" and user.is_active) or (purpose == "reset" and not user.is_active):
        raise PermissionDenied
    token = _issue(user, purpose)
    audit(actor_id, "password_link.issued", user.pk)
    return token


@transaction.atomic
def consume_link(token, purpose, new_password):
    company = current_company()
    try:
        data = signing.loads(token, salt="erp.password-link", max_age=3600)
        if data["company"] != str(company.pk) or data["purpose"] != purpose:
            raise PermissionDenied
        # Same lock order as membership changes; links cannot reactivate disabled reset targets.
        lock_access()
        link = PasswordLink.objects.select_for_update().get(pk=data["link"], user_id=data["user"], purpose=purpose, used_at__isnull=True, expires_at__gt=timezone.now())
        if not secrets.compare_digest(link.digest, hashlib.sha256(data["nonce"].encode()).hexdigest()):
            raise PermissionDenied
        user = get_user_model().objects.select_for_update().get(pk=link.user_id)
        if (purpose == "reset" and not user.is_active) or (purpose == "invite" and user.is_active):
            raise PermissionDenied
    except (signing.BadSignature, KeyError, ValueError, PasswordLink.DoesNotExist):
        raise PermissionDenied from None
    validate_password(new_password, user)
    user.set_password(new_password)
    if purpose == "invite":
        user.is_active = True
    user.save(update_fields=["password", "is_active"])
    PasswordLink.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
    audit(user.pk, "password_link.consumed", link.pk)
