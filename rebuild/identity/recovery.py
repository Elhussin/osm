import hashlib
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from access.services import lock_access
from .links import _issue
from .models import LoginThrottle


@transaction.atomic
def prepare_recovery(request, username):
    """Always called without revealing whether a local account exists."""
    if settings.INVITE_DELIVERY != "smtp":
        return None
    lock_access()
    key = hashlib.sha256(("reset|" + username.casefold() + "|" + request.META.get("REMOTE_ADDR", "")).encode()).hexdigest()
    throttle, _ = LoginThrottle.objects.get_or_create(key=key, defaults={"window_started": timezone.now()})
    if throttle.window_started < timezone.now() - timedelta(minutes=15):
        throttle.attempts = 0
        throttle.window_started = timezone.now()
    if throttle.attempts >= 3:
        return None
    throttle.attempts += 1
    throttle.save(update_fields=["attempts", "window_started"])
    user = get_user_model().objects.filter(username=username, is_active=True).first()
    if user is None or not user.email or not user.has_usable_password():
        return None
    return user, _issue(user, "reset")
