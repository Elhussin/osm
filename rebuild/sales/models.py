import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, F


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


class CashShift(models.Model):
    STATES = [("open", "مفتوحة"), ("review", "بانتظار اعتماد فرق الجرد"), ("closed", "مغلقة")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name="shifts")
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    register_snapshot = models.JSONField()
    currency = models.CharField(max_length=3, default="SAR")
    opening_cash = models.DecimalField(max_digits=18, decimal_places=2)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_cash_shifts")
    opened_at = models.DateTimeField(auto_now_add=True)
    custodian = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="held_cash_shifts")
    pending_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="incoming_cash_shifts")
    pending_cash = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    state = models.CharField(max_length=8, choices=STATES, default="open")
    version = models.PositiveIntegerField(default=1)
    expected_cash = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    counted_cash = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    difference = models.DecimalField(max_digits=18, decimal_places=2, null=True)
    closed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["register"], condition=Q(state__in=["open", "review"]), name="sales_one_unclosed_shift"),
            models.CheckConstraint(condition=Q(currency="SAR", version__gte=1, opening_cash__gte=0), name="sales_shift_identity"),
            models.CheckConstraint(condition=Q(pending_to__isnull=True, pending_cash__isnull=True) | (Q(state="open", pending_to__isnull=False, pending_cash__isnull=False, pending_cash__gte=0) & ~Q(pending_to=F("custodian"))), name="sales_shift_pending"),
            models.CheckConstraint(condition=Q(state="open", expected_cash__isnull=True, counted_cash__isnull=True, difference__isnull=True, closed_at__isnull=True) | (Q(expected_cash__isnull=False, expected_cash__gte=0, counted_cash__isnull=False, counted_cash__gte=0, difference__isnull=False, difference=F("counted_cash")-F("expected_cash"), pending_to__isnull=True, pending_cash__isnull=True) & ((Q(state="review", closed_at__isnull=True) & ~Q(difference=0)) | Q(state="closed", closed_at__isnull=False, closed_at__gte=F("opened_at")))), name="sales_shift_count_state"),
        ]

    @property
    def display_code(self):
        return str(self.pk)[:8].upper()


class ShiftEvent(models.Model):
    KINDS = [("opened", "فتح وردية"), ("handover_requested", "طلب تسليم عهدة"), ("handover_cancelled", "إلغاء طلب التسليم"), ("handover_rejected", "رفض استلام العهدة"), ("handover_accepted", "قبول استلام العهدة"), ("count_submitted", "تسجيل جرد الإغلاق"), ("variance_approved", "اعتماد فرق الجرد")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift = models.ForeignKey(CashShift, on_delete=models.PROTECT, related_name="events")
    version = models.PositiveIntegerField()
    kind = models.CharField(max_length=24, choices=KINDS)
    before = models.JSONField(default=dict)
    after = models.JSONField()
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    reason = models.CharField(max_length=300)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["shift", "version"], name="sales_shift_event_version"), models.CheckConstraint(condition=Q(version__gte=1, kind__in=["opened", "handover_requested", "handover_cancelled", "handover_rejected", "handover_accepted", "count_submitted", "variance_approved"]), name="sales_shift_event_kind")]
