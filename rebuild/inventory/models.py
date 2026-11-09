import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, F


class StockBalance(models.Model):
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    on_hand = models.BigIntegerField(default=0)
    reserved = models.BigIntegerField(default=0)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["variant", "branch"], name="inventory_balance_unique"), models.CheckConstraint(condition=Q(on_hand__gte=0, reserved__gte=0) & Q(reserved__lte=F("on_hand")), name="inventory_balance_nonnegative")]

    @property
    def available(self):
        return self.on_hand - self.reserved


class StockReceipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    kind = models.CharField(max_length=16, choices=[("receipt", "إضافة مخزون"), ("reversal", "عكس إضافة")])
    reverses = models.OneToOneField("self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversal")
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    reference = models.CharField(max_length=100, blank=True)
    reason = models.CharField(max_length=300)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(kind="receipt", reverses__isnull=True) | Q(kind="reversal", reverses__isnull=False), name="inventory_receipt_kind_valid")]


class StockMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(StockReceipt, null=True, on_delete=models.PROTECT, related_name="movements")
    reservation_event = models.OneToOneField("ReservationEvent", null=True, on_delete=models.PROTECT, related_name="movement")
    operation = models.ForeignKey("StockOperation", null=True, on_delete=models.PROTECT, related_name="movements")
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    delta = models.BigIntegerField()
    before = models.BigIntegerField()
    after = models.BigIntegerField()
    reserved_after = models.BigIntegerField()
    variant_snapshot = models.JSONField()

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(receipt__isnull=False, reservation_event__isnull=True, operation__isnull=True) | Q(receipt__isnull=True, reservation_event__isnull=False, operation__isnull=True) | Q(receipt__isnull=True, reservation_event__isnull=True, operation__isnull=False), name="inventory_movement_one_source"), models.UniqueConstraint(fields=["operation", "branch", "variant"], name="inventory_operation_branch_variant"), models.UniqueConstraint(fields=["receipt", "variant"], name="inventory_document_variant_unique"), models.CheckConstraint(condition=~Q(delta=0) & Q(before__gte=0, after__gte=0, reserved_after__gte=0) & Q(after=F("before") + F("delta")) & Q(reserved_after__lte=F("after")), name="inventory_movement_consistent")]


class StockOperation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=16, choices=[("transfer", "تحويل مخزون"), ("count", "جرد مخزون"), ("reversal", "عكس عملية مخزون")])
    source = models.ForeignKey("access.Branch", on_delete=models.PROTECT, related_name="stock_operations_from")
    destination = models.ForeignKey("access.Branch", null=True, on_delete=models.PROTECT, related_name="stock_operations_to")
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    quantity = models.BigIntegerField()
    reverses = models.OneToOneField("self", null=True, on_delete=models.PROTECT, related_name="reversal")
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    reference = models.CharField(max_length=100, blank=True)
    reason = models.CharField(max_length=300)
    before_values = models.JSONField()
    after_values = models.JSONField()
    variant_snapshot = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=0) & (Q(destination__isnull=True) | ~Q(source=F("destination"))), name="inventory_operation_quantity_branches"),
            models.CheckConstraint(condition=Q(kind="transfer", quantity__gt=0, destination__isnull=False, reverses__isnull=True) | Q(kind="count", destination__isnull=True, reverses__isnull=True) | Q(kind="reversal", reverses__isnull=False), name="inventory_operation_kind_valid"),
        ]


class StockReservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    quantity = models.BigIntegerField()
    held = models.BigIntegerField()
    issued = models.BigIntegerField(default=0)
    released = models.BigIntegerField(default=0)
    cancelled = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)
    reference = models.CharField(max_length=100, blank=True)
    variant_snapshot = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(quantity__gt=0, held__gte=0, issued__gte=0, released__gte=0) & Q(quantity=F("held") + F("issued") + F("released")) & (Q(cancelled=False) | Q(held=0)), name="inventory_reservation_consistent")]


class ReservationEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(StockReservation, on_delete=models.PROTECT, related_name="events")
    kind = models.CharField(max_length=16, choices=[("reserve", "حجز"), ("issue", "صرف"), ("release", "تحرير"), ("cancel", "إلغاء المتبقي"), ("reverse_issue", "عكس صرف")])
    quantity = models.BigIntegerField()
    version = models.PositiveIntegerField()
    held_after = models.BigIntegerField()
    issued_after = models.BigIntegerField()
    released_after = models.BigIntegerField()
    reverses = models.OneToOneField("self", null=True, on_delete=models.PROTECT, related_name="reversal")
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    reason = models.CharField(max_length=300)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["reservation", "version"], name="inventory_reservation_event_version"), models.CheckConstraint(condition=Q(quantity__gte=0, held_after__gte=0, issued_after__gte=0, released_after__gte=0) & (Q(kind="reverse_issue", reverses__isnull=False, quantity__gt=0) | Q(kind__in=["reserve", "issue", "release"], reverses__isnull=True, quantity__gt=0) | Q(kind="cancel", reverses__isnull=True)), name="inventory_reservation_event_valid")]
