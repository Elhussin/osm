import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, F, Func, Value
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators


class FiscalProfileRevision(models.Model):
    """Tenant-local seller data; never a certificate or proof of compliance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.PositiveIntegerField(unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    registration_status = models.CharField(max_length=20, choices=[("unknown", "لم يحدد"), ("registered", "مسجل في ضريبة القيمة المضافة"), ("not_registered", "غير مسجل")])
    vat_number = models.CharField(max_length=15, blank=True)
    commercial_registration = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=200, blank=True)
    building_number = models.CharField(max_length=4, blank=True)
    additional_number = models.CharField(max_length=4, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=5, blank=True)
    country_code = models.CharField(max_length=2, default="SA")
    currency = models.CharField(max_length=3, default="SAR")
    reason = models.CharField(max_length=300)
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gte=1, currency="SAR", country_code="SA"), name="finance_profile_scope"),
            models.CheckConstraint(condition=Q(registration_status="registered", vat_number__regex=r"^[0-9]{15}$") | Q(registration_status__in=["unknown", "not_registered"], vat_number=""), name="finance_profile_vat_shape"),
        ]


class Account(models.Model):
    KINDS = [("asset", "أصول"), ("liability", "التزامات"), ("equity", "حقوق ملكية"), ("revenue", "إيرادات"), ("expense", "مصروفات")]
    SIDES = [("debit", "مدين"), ("credit", "دائن")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=12, choices=KINDS)
    normal_side = models.CharField(max_length=6, choices=SIDES)
    is_group = models.BooleanField()
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    path = models.CharField(max_length=255, unique=True)
    depth = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(version__gte=1, depth__gte=1, depth__lte=8, kind__in=["asset", "liability", "equity", "revenue", "expense"], normal_side__in=["debit", "credit"]) & (Q(parent__isnull=True, depth=1) | Q(parent__isnull=False, depth__gt=1)) & (Q(parent__isnull=True) | ~Q(parent=F("id"))), name="finance_account_identity")]


class AccountingPeriod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    starts_on = models.DateField()
    ends_on = models.DateField()
    state = models.CharField(max_length=6, choices=[("open", "مفتوحة"), ("closed", "مغلقة")], default="open")
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(starts_on__lte=F("ends_on"), state__in=["open", "closed"], version__gte=1), name="finance_period_valid"),
            ExclusionConstraint(name="finance_period_no_overlap", expressions=[(Func(F("starts_on"), F("ends_on"), Value("[]"), function="DATERANGE", output_field=DateRangeField()), RangeOperators.OVERLAPS)]),
        ]


class SetupOperation(models.Model):
    KINDS = [("account_created", "إنشاء حساب"), ("account_renamed", "تسمية حساب"), ("account_activated", "تفعيل حساب"), ("account_disabled", "تعطيل حساب"), ("period_created", "إنشاء فترة"), ("period_closed", "إغلاق فترة"), ("period_reopened", "إعادة فتح فترة")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, null=True, on_delete=models.PROTECT, related_name="operations")
    period = models.ForeignKey(AccountingPeriod, null=True, on_delete=models.PROTECT, related_name="operations")
    kind = models.CharField(max_length=20, choices=KINDS)
    before = models.JSONField(default=dict)
    after = models.JSONField()
    reason = models.CharField(max_length=300)
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(account__isnull=False, period__isnull=True, kind__in=["account_created", "account_renamed", "account_activated", "account_disabled"]) | Q(account__isnull=True, period__isnull=False, kind__in=["period_created", "period_closed", "period_reopened"]), name="finance_setup_one_target")]
