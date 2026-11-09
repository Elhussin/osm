from django.urls import path
from .views import live, ready
from identity import views as identity

urlpatterns = [
    path("health/live/", live), path("health/ready/", ready),
    path("auth/login/", identity.sign_in, name="login"),
    path("auth/logout/", identity.sign_out, name="logout"),
    path("auth/link/<str:purpose>/", identity.password_link, name="password-link"),
    path("account/", identity.home, name="account-home"),
    path("account/branches/", identity.branches, name="account-branches"),
    path("account/branch/", identity.switch_branch, name="switch-branch"),
    path("account/audit/", identity.events, name="account-audit"),
]
