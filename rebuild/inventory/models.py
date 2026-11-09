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
    receipt = models.ForeignKey(StockReceipt, on_delete=models.PROTECT, related_name="movements")
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    delta = models.BigIntegerField()
    before = models.BigIntegerField()
    after = models.BigIntegerField()
    reserved_after = models.BigIntegerField()
    variant_snapshot = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["receipt", "variant"], name="inventory_document_variant_unique"), models.CheckConstraint(condition=~Q(delta=0) & Q(before__gte=0, after__gte=0, reserved_after__gte=0) & Q(after=F("before") + F("delta")) & Q(reserved_after__lte=F("after")), name="inventory_movement_consistent")]
