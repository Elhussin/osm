import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q, F

KINDS = [("frame", "إطار"), ("stock_lens", "عدسة مخزنية"), ("rx_lens", "عدسة تصنيع"), ("contact_lens", "عدسة لاصقة"), ("accessory", "إكسسوار"), ("device", "جهاز"), ("service", "خدمة")]
UNITS = [("piece", "قطعة / عدسة واحدة"), ("pair", "زوج عدسات"), ("box", "علبة"), ("service", "خدمة")]
CHANNELS = [("retail", "تجزئة"), ("wholesale", "جملة")]


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=KINDS)
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(kind__in=[key for key, _ in KINDS]), name="catalog_product_kind_valid")]


class Variant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    sku = models.CharField(max_length=60, unique=True)
    barcode = models.CharField(max_length=80, unique=True, blank=True, null=True)
    unit = models.CharField(max_length=12, choices=UNITS)
    specifications = models.JSONField()
    fingerprint = models.CharField(max_length=64)
    matrix_family = models.CharField(max_length=64, null=True, blank=True)
    sphere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def unit_label(self):
        if self.unit == "piece":
            return "عدسة واحدة" if self.product.kind in {"stock_lens", "rx_lens"} else "قطعة واحدة"
        return self.get_unit_display()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "fingerprint"], name="catalog_variant_specs_unique"), models.CheckConstraint(condition=Q(base_price__gte=0), name="catalog_base_price_nonnegative")]
        constraints += [models.UniqueConstraint(fields=["product", "matrix_family", "sphere", "cylinder"], condition=Q(matrix_family__isnull=False), name="catalog_matrix_cell_unique"), models.CheckConstraint(condition=Q(matrix_family__isnull=True, sphere__isnull=True, cylinder__isnull=True) | Q(matrix_family__isnull=False, sphere__isnull=False, cylinder__isnull=False), name="catalog_matrix_fields_together")]
        indexes = [models.Index(fields=["product", "matrix_family"], name="catalog_matrix_family_idx")]


class PriceRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT, related_name="price_rules")
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT, null=True, blank=True)
    customer = models.ForeignKey("clinical.Customer", on_delete=models.PROTECT, null=True, blank=True)
    channel = models.CharField(max_length=12, choices=CHANNELS, default="retail")
    min_quantity = models.PositiveIntegerField(default=1)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="catalog_rule_price_nonnegative"),
            models.CheckConstraint(condition=Q(min_quantity__gte=1) & Q(min_quantity__lte=1000000), name="catalog_rule_quantity_range"),
            models.CheckConstraint(condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")), name="catalog_rule_dates_order"),
            models.CheckConstraint(condition=Q(customer__isnull=True) | Q(branch__isnull=False), name="catalog_customer_rule_branch"),
            models.UniqueConstraint(fields=["variant", "channel", "min_quantity", "valid_from"], condition=Q(active=True, branch__isnull=True, customer__isnull=True), name="catalog_global_rule_unique"),
            models.UniqueConstraint(fields=["variant", "branch", "channel", "min_quantity", "valid_from"], condition=Q(active=True, branch__isnull=False, customer__isnull=True), name="catalog_branch_rule_unique"),
            models.UniqueConstraint(fields=["variant", "branch", "customer", "channel", "min_quantity", "valid_from"], condition=Q(active=True, customer__isnull=False), name="catalog_customer_rule_unique"),
            models.CheckConstraint(condition=Q(channel__in=[key for key, _ in CHANNELS]), name="catalog_channel_valid"),
        ]
