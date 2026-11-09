# core/permissions/has_permission.py
from rest_framework.permissions import BasePermission
from core.permissions.roles import Role
from core.permissions.permissions import ROLE_PERMISSIONS

class HasPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        required_permission = getattr(view, 'required_permission', None)

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        try:
            role = Role[user.role]
        except (KeyError, AttributeError):
            return False

        allowed_permissions = ROLE_PERMISSIONS.get(role, [])
        return allowed_permissions == '__all__' or required_permission in allowed_permissions
