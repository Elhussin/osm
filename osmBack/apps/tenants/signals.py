from django.db.models.signals import pre_save
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.tenants.models import Branch

User = get_user_model()

@receiver(pre_save, sender=User)
def check_user_limit(sender, instance, **kwargs):
    tenant = getattr(instance, 'tenant', None)
    if tenant:
        current_count = User.objects.filter(tenant=tenant).exclude(pk=instance.pk).count()
        if current_count >= tenant.max_users:
            raise ValidationError("You have reached the maximum number of users for your plan.")

@receiver(pre_save, sender=Branch)
def check_branch_limit(sender, instance, **kwargs):
    tenant = getattr(instance, 'tenant', None)
    if tenant:
        current_count = Branch.objects.filter(tenant=tenant).exclude(pk=instance.pk).count()
        if current_count >= tenant.max_branches:
            raise ValidationError("You have reached the maximum number of branches for your plan.")
