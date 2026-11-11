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


class TaxTreatmentRevision(models.Model):
    STATES = [("reviewed", "مراجع داخليًا"), ("blocked", "محظور لحين المراجعة")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT, related_name="tax_revisions")
    version = models.PositiveIntegerField()
    valid_from = models.DateField()
    state = models.CharField(max_length=10, choices=STATES)
    category = models.CharField(max_length=1, blank=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    reason_code = models.CharField(max_length=32, blank=True)
    reason_text = models.CharField(max_length=300, blank=True)
    basis = models.CharField(max_length=500)
    reason = models.CharField(max_length=300)
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["variant", "version"], name="sales_tax_revision_version"),
            models.CheckConstraint(condition=Q(version__gte=1, valid_from__gte="2020-07-01") & (Q(state="blocked", category="", rate__isnull=True, reason_code="", reason_text="") | (Q(state="reviewed", rate__isnull=False) & (Q(category="S", rate=15, reason_code="", reason_text="") | (Q(category__in=["Z", "E", "O"], rate=0) & ~Q(reason_code="") & ~Q(reason_text=""))))), name="sales_tax_revision_shape")]


class TaxQuote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    customer = models.ForeignKey("clinical.Customer", null=True, on_delete=models.PROTECT)
    fiscal_profile = models.ForeignKey("finance.FiscalProfileRevision", on_delete=models.PROTECT)
    as_of = models.DateField()
    currency = models.CharField(max_length=3, default="SAR")
    payload = models.JSONField()
    net = models.DecimalField(max_digits=18, decimal_places=2)
    vat = models.DecimalField(max_digits=18, decimal_places=2)
    tax_inclusive = models.DecimalField(max_digits=18, decimal_places=2)
    payable_rounding = models.DecimalField(max_digits=18, decimal_places=2)
    payable = models.DecimalField(max_digits=18, decimal_places=2)
    reason = models.CharField(max_length=300)
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(currency="SAR", as_of__gte="2020-07-01", net__gte=0, vat__gte=0, tax_inclusive=F("net")+F("vat"), payable=F("tax_inclusive")+F("payable_rounding"), payable__gte=0, payable_rounding__gte="-0.01", payable_rounding__lte="0.01"), name="sales_tax_quote_totals")]


class SaleOrder(models.Model):
    STATES = [("draft", "مسودة"), ("confirmed", "مؤكد"), ("cancelled", "ملغى")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    customer = models.ForeignKey("clinical.Customer", on_delete=models.PROTECT)
    shift = models.ForeignKey(CashShift, on_delete=models.PROTECT)
    state = models.CharField(max_length=10, choices=STATES, default="draft")
    version = models.PositiveIntegerField(default=1)
    current_revision = models.ForeignKey("OrderRevision", null=True, on_delete=models.PROTECT, related_name="current_for")
    confirmed_quote = models.OneToOneField(TaxQuote, null=True, on_delete=models.PROTECT, related_name="confirmed_order")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(version__gte=1, state__in=["draft", "confirmed", "cancelled"]) & (Q(state="draft", confirmed_quote__isnull=True) | Q(state="confirmed", confirmed_quote__isnull=False) | Q(state="cancelled")), name="sales_order_state")]


class OrderRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(SaleOrder, on_delete=models.PROTECT, related_name="revisions")
    version = models.PositiveIntegerField()
    quote = models.OneToOneField(TaxQuote, on_delete=models.PROTECT, related_name="order_revision")
    prescription_revision = models.ForeignKey("clinical.PrescriptionRevision", null=True, on_delete=models.PROTECT)
    snapshot = models.JSONField()
    positions = models.JSONField(default=list)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "version"], name="sales_order_revision_version"), models.CheckConstraint(condition=Q(version__gte=1), name="sales_order_revision_positive")]


class OrderEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(SaleOrder, on_delete=models.PROTECT, related_name="events")
    version = models.PositiveIntegerField()
    kind = models.CharField(max_length=12, choices=[("saved", "حفظ مسودة"), ("confirmed", "تأكيد وحجز"), ("cancelled", "إلغاء وتحرير")])
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    reason = models.CharField(max_length=300)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "version"], name="sales_order_event_version"), models.CheckConstraint(condition=Q(version__gte=1, kind__in=["saved", "confirmed", "cancelled"]), name="sales_order_event_kind")]


class OrderHold(models.Model):
    revision = models.ForeignKey(OrderRevision, on_delete=models.PROTECT, related_name="holds")
    position = models.PositiveSmallIntegerField()
    reservation = models.OneToOneField("inventory.StockReservation", on_delete=models.PROTECT, related_name="sale_hold")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["revision", "position"], name="sales_order_hold_line"), models.CheckConstraint(condition=Q(position__gte=1, position__lte=40), name="sales_order_hold_position")]
