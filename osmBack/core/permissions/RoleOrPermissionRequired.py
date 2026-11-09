from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from django.utils.translation import gettext_lazy as T


class RoleOrPermissionRequired(BasePermission):
    """
    DRF permission class that supports:
    - allowed_roles
    - required_permissions
    - require_all
    - super_roles
    Can be used directly in permission_classes with arguments.
    """
    def __init__(self, allowed_roles=None, required_permissions=None, require_all=False, super_roles=None):
        self.allowed_roles = allowed_roles or []
        self.required_permissions = required_permissions or []
        self.require_all = require_all
        self.super_roles = super_roles or ["admin", "owner"]

    def __call__(self):
        return self
    def has_permission(self, request, view):    
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise NotAuthenticated(detail=T("Not authenticated. Please login first"))
        if not user.is_active:
            raise PermissionDenied(detail=T("Account disabled. Please contact admin."))

        # Django superuser
        if user.is_superuser:
            return True

        # Check user role
        user_role = getattr(user, "role", None)
        role_name = getattr(user_role, "name", None)

        # If user is in super roles list
        if role_name in self.super_roles:
            return True

        # Check if user role is in allowed roles list
        if self.allowed_roles and role_name in self.allowed_roles:
            return True

        # Check if user has required permissions
        if self.required_permissions and user_role:
            user_permissions = set(user_role.permissions.values_list("code", flat=True))
            required_perms = set(self.required_permissions)

            if self.require_all:
                # User must have all permissions
                if required_perms.issubset(user_permissions):
                    return True
                else:
                    missing = required_perms - user_permissions
                    raise PermissionDenied(
                        detail=T(f"❌ You are missing the following permissions: {', '.join(missing)}.")
                    )
            else:
                # User must have at least one permission
                if user_permissions.intersection(required_perms):
                    return True
                else:
                    raise PermissionDenied(
                        detail=T(f"❌ You are missing the following permissions: {', '.join(required_perms)}.")
                    )

        # لا يوجد أي تطابق في الدور أو الصلاحيات
        raise PermissionDenied(detail="❌ You are missing the following permissions: {', '.join(required_perms)}.")

    @classmethod
    def with_requirements(cls, allowed_roles=None, required_permissions=None, require_all=False, super_roles=None):
        """Helper for easy inline usage in DRF views"""
        return type(f"{cls.__name__}_Custom", (cls,), {})(allowed_roles, required_permissions, require_all, super_roles)


    # permission_classes = [
    #     RoleOrPermissionRequired.with_requirements(
    #         allowed_roles=["doctor", "pharmacist"],
    #         required_permissions=["create_prescription", "approve_prescription"],
    #         require_all=False, 
    #         super_roles=["admin", "owner"]  # 👈 لهم سماح كامل
    #     )
    # ]

        # permission_classes = [
        # RoleOrPermissionRequired(
        #     allowed_roles=["staff"],
        #     required_permissions=["view_users"]
        # )
    # ]


    #     permission_classes = [
    #     RoleOrPermissionRequired.with_requirements(super_roles=["admin", "owner"])
    # ]