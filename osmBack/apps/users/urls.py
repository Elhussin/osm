
from django.urls import path
from .views import( LoginView, RegisterView, LogoutView, RefreshTokenView, HealthCheckView,
ProfileView,UserViewSet,RequestPasswordResetView,PasswordResetConfirmView,PageViewSet,PublicPageViewSet,
ContactUsViewSet,TenantSettingsViewset,
PermissionViewSet, RolePermissionViewSet, RoleViewSet)
from rest_framework.routers import DefaultRouter
from django.urls import include


router = DefaultRouter()

router.register(r'users', UserViewSet, basename='users')
router.register(r'permissions', PermissionViewSet, basename='permissions')
router.register(r'role-permissions', RolePermissionViewSet, basename='role-permissions')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'pages', PageViewSet, basename='pages')  
router.register(r'public/pages', PublicPageViewSet, basename='public-pages')  # GET by slug                                                                                                                                                                                                                   
router.register(r'contact-us', ContactUsViewSet, basename='contact-us')
router.register(r'tenant-settings', TenantSettingsViewset, basename='tenant-settings')



urlpatterns = [
    path("", include(router.urls)),
    path("health/", HealthCheckView.as_view()),
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("token/refresh/", RefreshTokenView.as_view()),
    path("profile/", ProfileView.as_view()),
    path('password-reset/', RequestPasswordResetView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

]

    # path('api/pages/', PageListCreateView.as_view()),
    # path('api/pages/<int:pk>/', PageDetailView.as_view()),
    # path('api/pages/slug/<slug:slug>/', PageBySlugView.as_view()),


