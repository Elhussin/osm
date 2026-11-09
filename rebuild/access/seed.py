from .models import AccessLock, Role
from .policy import ROLES


def seed_access():
    AccessLock.objects.get_or_create(pk=1)
    for code in ROLES:
        Role.objects.get_or_create(code=code)
