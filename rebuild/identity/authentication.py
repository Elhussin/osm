import hashlib
from datetime import timedelta
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from access.authorization import current_company
from .models import LoginThrottle


@transaction.atomic
def authenticate_limited(request, username, password):
    current_company()
    # Scope is already the tenant schema; do not store the attempted username/IP.
    key = hashlib.sha256((username.casefold() + "|" + request.META.get("REMOTE_ADDR", "")).encode()).hexdigest()
    LoginThrottle.objects.get_or_create(key=key, defaults={"window_started": timezone.now()})
    throttle = LoginThrottle.objects.select_for_update().get(pk=key)
    if throttle.window_started < timezone.now() - timedelta(minutes=15):
        throttle.attempts = 0
        throttle.window_started = timezone.now()
    if throttle.attempts >= 5:
        return None
    user = authenticate(request, username=username, password=password)
    throttle.attempts = 0 if user else throttle.attempts + 1
    throttle.save(update_fields=["attempts", "window_started"])
    return user
