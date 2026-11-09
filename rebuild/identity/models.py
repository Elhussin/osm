import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Company-bound by schema; never migrated to public or linked across companies."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
