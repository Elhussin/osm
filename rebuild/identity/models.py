import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Company-bound by schema; never migrated to public or linked across companies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class PasswordLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    purpose = models.CharField(max_length=20, choices=[("invite", "Invite"), ("reset", "Reset")])
    digest = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True)


class LoginThrottle(models.Model):
    key = models.CharField(primary_key=True, max_length=64)
    attempts = models.PositiveIntegerField(default=0)
    window_started = models.DateTimeField()
