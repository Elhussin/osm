from django.urls import path
from .views import live, ready
from identity import views as identity
from workspace import views as workspace

urlpatterns = [
    path("health/live/", live), path("health/ready/", ready),
    path("auth/login/", identity.sign_in, name="login"),
    path("auth/logout/", identity.sign_out, name="logout"),
    path("auth/recovery/", identity.recovery, name="recovery"),
    path("auth/link/<str:purpose>/", identity.password_link, name="password-link"),
    path("", workspace.overview),
    path("account/", workspace.overview, name="account-home"),
    path("account/branches/", workspace.branches, name="account-branches"),
    path("account/branches/new/", workspace.branch_form, name="branch-new"),
    path("account/branches/<uuid:branch_id>/", workspace.branch_form, name="branch-edit"),
    path("account/branches/<uuid:branch_id>/state/", workspace.branch_state, name="branch-state"),
    path("account/branch/", identity.switch_branch, name="switch-branch"),
    path("account/audit/", workspace.events, name="account-audit"),
    path("account/members/", workspace.members, name="members"),
    path("account/members/invite/", workspace.invite, name="invite-member"),
    path("account/members/<uuid:member_id>/", workspace.member_detail, name="member-detail"),
    path("account/members/<uuid:member_id>/state/", workspace.member_state, name="member-state"),
    path("account/members/<uuid:member_id>/roles/", workspace.member_role, name="member-role"),
    path("account/members/<uuid:member_id>/roles/<int:assignment_id>/revoke/", workspace.revoke_assignment, name="revoke-assignment"),
    path("account/members/<uuid:member_id>/access/", workspace.member_branch_access, name="member-access"),
    path("account/members/<uuid:member_id>/send/<str:purpose>/", workspace.resend_link, name="resend-link"),
    path("account/roles/", workspace.roles, name="roles"),
    path("account/ownership/", workspace.ownership, name="ownership"),
]

handler403 = workspace.error_page
handler404 = lambda request, exception: workspace.error_page(request, exception, status=404)
handler500 = lambda request: workspace.error_page(request, status=500)
