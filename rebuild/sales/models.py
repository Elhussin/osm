import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class CashRegister(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    cash_account = models.OneToOneField("finance.Account", on_delete=models.PROTECT)
    currency = models.CharField(max_length=3, default="SAR")
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "code"], name="sales_register_branch_code"),
            models.CheckConstraint(condition=Q(version__gte=1, currency="SAR", code__regex=r"^[A-Z0-9][A-Z0-9-]*$"), name="sales_register_valid"),
        ]


class RegisterOperation(models.Model):
    KINDS = [("created", "إنشاء صندوق"), ("renamed", "تغيير اسم الصندوق"), ("activated", "تفعيل صندوق"), ("disabled", "تعطيل صندوق")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name="operations")
    kind = models.CharField(max_length=12, choices=KINDS)
    before = models.JSONField(default=dict)
    after = models.JSONField()
    reason = models.CharField(max_length=300)
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(kind__in=["created", "renamed", "activated", "disabled"]), name="sales_register_operation_kind")]
