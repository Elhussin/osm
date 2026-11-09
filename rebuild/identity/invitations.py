from django.contrib.auth import get_user_model
from django.db import transaction
from access.authorization import require
from access.services import lock_access, audit, assign_role
from .links import issue_link


@transaction.atomic
def invite_member(actor_id, *, username, email, role_code, branch_id=None):
    lock_access()
    require(actor_id, "members.manage")
    user = get_user_model()(username=username, email=email, is_active=False)
    user.set_unusable_password()
    user.full_clean()
    user.save()
    assign_role(actor_id, user_id=user.pk, role_code=role_code, branch_id=branch_id)
    token = issue_link(actor_id, user.pk, "invite")
    audit(actor_id, "member.invited", user.pk)
    return user, token
