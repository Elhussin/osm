from .views import *
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'branch-users', BranchUsersViewSet, basename='branch-user')

urlpatterns = [
    path('', include(router.urls)),
]
