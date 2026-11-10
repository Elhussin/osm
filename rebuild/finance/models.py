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
    state = models.CharField(max_length=6, choices=[("open", "مفتوحة"), ("closed", "مغلقة"), ("void", "ملغاة")], default="open")
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(starts_on__lte=F("ends_on"), state__in=["open", "closed", "void"], version__gte=1), name="finance_period_valid"),
            ExclusionConstraint(name="finance_period_no_overlap", expressions=[(Func(F("starts_on"), F("ends_on"), Value("[]"), function="DATERANGE", output_field=DateRangeField()), RangeOperators.OVERLAPS)], condition=~Q(state="void")),
        ]


class SetupOperation(models.Model):
    KINDS = [("account_created", "إنشاء حساب"), ("account_renamed", "تسمية حساب"), ("account_activated", "تفعيل حساب"), ("account_disabled", "تعطيل حساب"), ("period_created", "إنشاء فترة"), ("period_closed", "إغلاق فترة"), ("period_reopened", "إعادة فتح فترة"), ("period_voided", "إلغاء فترة غير مستخدمة")]
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
        constraints = [models.CheckConstraint(condition=Q(account__isnull=False, period__isnull=True, kind__in=["account_created", "account_renamed", "account_activated", "account_disabled"]) | Q(account__isnull=True, period__isnull=False, kind__in=["period_created", "period_closed", "period_reopened", "period_voided"]), name="finance_setup_one_target")]


class JournalDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    state = models.CharField(max_length=9, choices=[("draft", "مسودة"), ("posted", "مرحّلة"), ("cancelled", "ملغاة")], default="draft")
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(state__in=["draft", "posted", "cancelled"], version__gte=1), name="finance_draft_valid")]


class JournalRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.ForeignKey(JournalDraft, on_delete=models.PROTECT, related_name="revisions")
    version = models.PositiveIntegerField()
    entry_date = models.DateField()
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT, related_name="journal_revisions")
    reference = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=300)
    lines = models.JSONField()
    total_debit = models.DecimalField(max_digits=18, decimal_places=2)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default="SAR")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["draft", "version"], name="finance_draft_revision_unique"), models.CheckConstraint(condition=Q(version__gte=1, total_debit__gte=0, total_credit__gte=0, currency="SAR"), name="finance_revision_valid")]


class JournalCounter(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    next_number = models.BigIntegerField(default=1)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(id=1, next_number__gte=1), name="finance_counter_valid")]


class JournalEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.BigIntegerField(unique=True)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    period = models.ForeignKey(AccountingPeriod, on_delete=models.PROTECT, related_name="journal_entries")
    entry_date = models.DateField()
    draft = models.OneToOneField(JournalDraft, null=True, on_delete=models.PROTECT, related_name="posted_entry")
    revision = models.OneToOneField(JournalRevision, null=True, on_delete=models.PROTECT, related_name="posted_entry")
    reverses = models.OneToOneField("self", null=True, on_delete=models.PROTECT, related_name="reversal")
    reference = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=300)
    total_debit = models.DecimalField(max_digits=18, decimal_places=2)
    total_credit = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default="SAR")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(number__gte=1, total_debit__gt=0, total_credit=F("total_debit"), currency="SAR") & (Q(draft__isnull=False, revision__isnull=False, reverses__isnull=True) | Q(draft__isnull=True, revision__isnull=True, reverses__isnull=False)) & (Q(reverses__isnull=True) | ~Q(reverses=F("id"))), name="finance_posted_entry_valid")]

    @property
    def display_number(self):
        return f"JE-{self.number:08d}"


class JournalLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    position = models.PositiveSmallIntegerField()
    debit = models.DecimalField(max_digits=18, decimal_places=2)
    credit = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.CharField(max_length=300, blank=True)
    account_snapshot = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["entry", "position"], name="finance_journal_line_position"), models.CheckConstraint(condition=Q(position__gte=1, position__lte=40) & (Q(debit__gt=0, credit=0) | Q(credit__gt=0, debit=0)), name="finance_journal_line_valid")]


class JournalOperation(models.Model):
    KINDS = [("draft_created", "إنشاء مسودة"), ("draft_revised", "حفظ إصدار مسودة"), ("draft_cancelled", "إلغاء مسودة"), ("journal_posted", "ترحيل قيد"), ("journal_reversed", "عكس قيد")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.ForeignKey(JournalDraft, null=True, on_delete=models.PROTECT, related_name="operations")
    entry = models.ForeignKey(JournalEntry, null=True, on_delete=models.PROTECT, related_name="operations")
    kind = models.CharField(max_length=20, choices=KINDS)
    draft_version = models.PositiveIntegerField(null=True)
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    reason = models.CharField(max_length=300)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["draft", "draft_version"], name="finance_journal_operation_version"), models.CheckConstraint(condition=Q(draft__isnull=False, entry__isnull=True, kind__in=["draft_created", "draft_revised", "draft_cancelled"], draft_version__isnull=False, draft_version__gte=1) | Q(draft__isnull=False, entry__isnull=False, kind="journal_posted", draft_version__isnull=False, draft_version__gte=1) | Q(draft__isnull=True, entry__isnull=False, kind="journal_reversed", draft_version__isnull=True), name="finance_journal_operation_target")]
