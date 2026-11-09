from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from access.authorization import require, current_company, visible_branches
from access.services import audit, lock_access
from clinical.models import CustomerBranchAccess
from .models import Product, Variant, PriceRule, CHANNELS
from .specifications import code, money, canonical_specs


def quantity(value):
    try:
        if isinstance(value, (bool, float)):
            raise ValueError
        number = Decimal(value)
        if not number.is_finite() or not 1 <= number <= 1000000 or number != number.to_integral_value():
            raise ValueError
        return int(number)
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("الكمية عدد صحيح بين 1 و1000000 بوحدة بيع المتغير.") from None


@transaction.atomic
def create_product(actor_id, *, code_value, name, kind, brand="", model=""):
    lock_access()
    require(actor_id, "catalog.manage")
    product = Product(code=code(code_value, 40), name=name.strip(), kind=kind, brand=brand.strip(), model=model.strip(), created_by_id=actor_id)
    product.full_clean()
    product.save()
    audit(actor_id, "catalog.product_created", product.pk)
    return product


@transaction.atomic
def update_product(actor_id, *, product_id, expected_version, name, brand, model, active):
    lock_access()
    require(actor_id, "catalog.manage")
    product = Product.objects.select_for_update().get(pk=product_id)
    if product.version != expected_version:
        raise ValidationError("تغير المنتج في جلسة أخرى. حدّث الصفحة.")
    product.name, product.brand, product.model, product.active = name.strip(), brand.strip(), model.strip(), active
    product.version += 1
    product.full_clean()
    product.save(update_fields=["name", "brand", "model", "active", "version"])
    audit(actor_id, "catalog.product_updated", product.pk)
    return product


@transaction.atomic
def create_variant(actor_id, *, product_id, sku, barcode="", unit, base_price, specifications):
    lock_access()
    require(actor_id, "catalog.manage")
    product = Product.objects.select_for_update().get(pk=product_id, active=True)
    packed, fingerprint = canonical_specs(product.kind, specifications, unit)
    if Variant.objects.filter(product=product, fingerprint=fingerprint).exists():
        raise ValidationError("يوجد متغير بالمواصفات ووحدة البيع نفسيهما. استخدمه أو غيّر المواصفات.")
    variant = Variant(product=product, sku=code(sku), barcode=code(barcode, 80) if barcode else None, unit=unit,
        base_price=money(base_price), specifications=packed, fingerprint=fingerprint, created_by_id=actor_id)
    variant.full_clean()
    variant.save()
    audit(actor_id, "catalog.variant_created", variant.pk)
    return variant


@transaction.atomic
def update_variant(actor_id, *, variant_id, expected_version, base_price, active):
    lock_access()
    require(actor_id, "catalog.manage")
    variant = Variant.objects.select_for_update().get(pk=variant_id)
    if variant.version != expected_version:
        raise ValidationError("تغير المتغير في جلسة أخرى. حدّث الصفحة.")
    variant.base_price, variant.active = money(base_price), active
    variant.version += 1
    variant.full_clean()
    variant.save(update_fields=["base_price", "active", "version"])
    audit(actor_id, "catalog.variant_updated", variant.pk)
    return variant


def _rule_scope(actor_id, branch_id, customer_id):
    if branch_id:
        require(actor_id, "catalog.manage", [branch_id])
    if customer_id:
        if not branch_id:
            raise ValidationError({"branch_id": "حدد الفرع لسعر العميل."})
        require(actor_id, "customer.read", [branch_id])
        if not CustomerBranchAccess.objects.filter(customer_id=customer_id, branch_id=branch_id, customer__active=True).exists():
            raise PermissionDenied


@transaction.atomic
def create_price_rule(actor_id, *, variant_id, branch_id=None, customer_id=None, channel="retail", min_quantity=1, valid_from=None, valid_until=None, unit_price):
    lock_access()
    require(actor_id, "catalog.manage")
    _rule_scope(actor_id, branch_id, customer_id)
    variant = Variant.objects.get(pk=variant_id, active=True, product__active=True)
    start = models.DateField().to_python(valid_from)
    end = models.DateField().to_python(valid_until) if valid_until else None
    rule = PriceRule(variant=variant, branch_id=branch_id, customer_id=customer_id, channel=channel, min_quantity=quantity(min_quantity),
        valid_from=start, valid_until=end, unit_price=money(unit_price), created_by_id=actor_id)
    rule.full_clean(validate_constraints=False)
    if end and end < start:
        raise ValidationError({"valid_until": "نهاية الفترة لا تسبق بدايتها."})
    overlaps = PriceRule.objects.filter(variant=variant, branch_id=branch_id, customer_id=customer_id, channel=channel, min_quantity=rule.min_quantity, active=True)
    if end:
        overlaps = overlaps.filter(valid_from__lte=end)
    overlaps = overlaps.filter(Q(valid_until__isnull=True) | Q(valid_until__gte=start))
    if overlaps.exists():
        raise ValidationError("تتداخل هذه الفترة مع قاعدة نشطة للنطاق والقناة وحد الكمية نفسيهما. أوقف السابقة أو اختر فترة مختلفة.")
    rule.validate_constraints()
    rule.save()
    audit(actor_id, "catalog.price_rule_created", rule.pk)
    return rule


@transaction.atomic
def disable_price_rule(actor_id, *, rule_id):
    lock_access()
    require(actor_id, "catalog.manage")
    rule = PriceRule.objects.select_for_update().get(pk=rule_id)
    _rule_scope(actor_id, rule.branch_id, rule.customer_id)
    if rule.active:
        rule.active = False
        rule.save(update_fields=["active"])
        audit(actor_id, "catalog.price_rule_disabled", rule.pk)


def price_rules_for(actor_id, variant):
    require(actor_id, "catalog.manage")
    rows = variant.price_rules.select_related("branch", "customer").order_by("-active", "-valid_from", "id")
    visible = visible_branches(actor_id, "catalog.manage").values_list("pk", flat=True)
    customer_visible = visible_branches(actor_id, "customer.read").values_list("pk", flat=True)
    return rows.filter(Q(branch__isnull=True) | Q(branch_id__in=visible)).filter(Q(customer__isnull=True) | Q(branch_id__in=customer_visible))


def quote_price(actor_id, *, variant_id, branch_id, customer_id=None, channel="retail", count=1, as_of=None):
    # Revalidated for every quote. A returned dictionary is a snapshot, never authority to post a sale.
    require(actor_id, "catalog.read")
    require(actor_id, "invoice.read", [branch_id])
    if channel not in dict(CHANNELS):
        raise ValidationError("قناة التسعير غير صالحة.")
    count = quantity(count)
    day = models.DateField().to_python(as_of) if as_of else timezone.localdate()
    if customer_id:
        require(actor_id, "customer.read", [branch_id])
        if not CustomerBranchAccess.objects.filter(customer_id=customer_id, branch_id=branch_id, customer__active=True).exists():
            raise PermissionDenied
    variant = Variant.objects.select_related("product").get(pk=variant_id, active=True, product__active=True)
    rules = list(PriceRule.objects.filter(variant=variant, active=True, channel=channel, min_quantity__lte=count, valid_from__lte=day)
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=day))
        .filter(Q(branch__isnull=True) | Q(branch_id=branch_id))
        .filter(Q(customer__isnull=True) | Q(customer_id=customer_id)))
    rank = lambda rule: (int(rule.customer_id is not None), int(rule.branch_id is not None), rule.min_quantity)
    rules.sort(key=rank, reverse=True)
    if len(rules) > 1 and rank(rules[0]) == rank(rules[1]):
        raise ValidationError("توجد قواعد أسعار متعارضة. راجع مسؤول الدليل قبل متابعة البيع.")
    chosen = rules[0] if rules else None
    price = chosen.unit_price if chosen is not None else variant.base_price
    return {"company_id": str(current_company().pk), "variant_id": str(variant.pk), "sku": variant.sku,
        "product": variant.product.name, "unit": variant.unit, "unit_label": variant.unit_label, "quantity": count,
        "currency": "SAR", "tax_basis": "exclusive", "channel": channel, "as_of": day.isoformat(),
        "branch_id": str(branch_id), "customer_id": str(customer_id) if customer_id else None,
        "unit_price": format(price, ".2f"), "total": format((price * count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f"),
        "rule_id": str(chosen.pk) if chosen else None, "source": "customer" if chosen and chosen.customer_id else ("branch" if chosen and chosen.branch_id else ("general" if chosen else "base")),
        "variant_version": variant.version, "specifications": variant.specifications}
