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


class LinkDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link = models.OneToOneField(PasswordLink, on_delete=models.PROTECT)
    url_base = models.URLField(max_length=500)
    recipient = models.EmailField()
    company_name = models.CharField(max_length=200)
    actor_id = models.UUIDField(null=True)
    status = models.CharField(max_length=20, default="pending")
    attempts = models.PositiveSmallIntegerField(default=0)
    available_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True)
