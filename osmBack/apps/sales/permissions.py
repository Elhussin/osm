# permissions.py

from rest_framework.permissions import BasePermission

class IsBranchManagerOrReadOnly(BasePermission):
    """
    يسمح فقط لمدير الفرع بالوصول الكامل، والبقية قراءة فقط.
    """

    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return hasattr(request.user, 'branchusers') and request.user.branchusers.role == 'manager'

class IsOwnerBranch(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.branch == request.user.branchusers.branch
