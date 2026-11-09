from django.utils import timezone
from datetime import timedelta

def expiration_date(days=1):
    return timezone.now() + timedelta(days=days)
