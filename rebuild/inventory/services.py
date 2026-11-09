from decimal import Decimal
import uuid
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from access.authorization import require, current_company, visible_branches, authorization_state
from access.policy import permits, ResourceScope
from access.services import lock_access, audit
from catalog.models import Product, Variant
from catalog.specifications import canonical_specs, stock_matrix_fields
from .models import StockBalance, StockReceipt, StockMovement
from .matrix import normalize_cells, digest


def receipts_for(actor_id):
    return StockReceipt.objects.filter(branch__in=visible_branches(actor_id, "stock.read"))


def _payload(actor_id, *, product_id, template_id, branch_id, cells, operation_key, template_version, create_missing=False, reference="", reason=""):
    normalized = normalize_cells(cells)
    try:
        payload = {"company_id": str(current_company().pk), "actor_id": str(actor_id), "product_id": str(uuid.UUID(str(product_id))),
            "template_id": str(uuid.UUID(str(template_id))), "branch_id": str(uuid.UUID(str(branch_id))), "operation_key": str(uuid.UUID(str(operation_key))),
            "template_version": int(template_version), "create_missing": create_missing, "reference": reference.strip(), "reason": reason.strip(), "cells": normalized}
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("معرفات العملية أو قالب الصنف غير صالحة.") from None
    if not isinstance(create_missing, bool) or not payload["reason"] or len(payload["reason"]) > 300 or len(payload["reference"]) > 100:
        raise ValidationError("حدد سبب الإضافة حتى300 حرف ومرجعًا اختياريًا حتى100 حرف.")
    return payload


def _require(actor_id, payload):
    state = authorization_state(actor_id)
    if state is None:
        raise PermissionDenied
    principal, context, grants = state
    checks = [("catalog.read", frozenset()), ("stock.read", frozenset([payload["branch_id"]])), ("stock.receive", frozenset([payload["branch_id"]]))]
    if payload["create_missing"]:
        checks.append(("catalog.manage", frozenset()))
    if not all(permits(principal, context, action, ResourceScope(context.company_id, branches), grants) for action, branches in checks):
        raise PermissionDenied


def _plan(actor_id, payload, *, authorized=False):
    if not authorized:
        _require(actor_id, payload)
    product = Product.objects.get(pk=payload["product_id"], kind="stock_lens", active=True)
    template = Variant.objects.select_related("product").get(pk=payload["template_id"], product=product, active=True)
    if template.version != payload["template_version"]:
        raise ValidationError("تغير سعر القالب أو حالته. حدّث المصفوفة وأعد المعاينة.")
    if template.matrix_family != stock_matrix_fields(template.specifications)["matrix_family"]:
        raise ValidationError("فهرس عائلة العدسات غير متسق. راجع مسؤول النظام.")
    cells = payload["cells"]
    variants = {(v.sphere, v.cylinder): v for v in Variant.objects.filter(product=product, matrix_family=template.matrix_family,
        sphere__in={row["sphere"] for row in cells}, cylinder__in={row["cylinder"] for row in cells})}
    existing = [variant.pk for variant in variants.values()]
    balances = {balance.variant_id: balance for balance in StockBalance.objects.filter(branch_id=payload["branch_id"], variant_id__in=existing)}
    lines = []
    for row in cells:
        coordinate = (Decimal(row["sphere"]), Decimal(row["cylinder"]))
        variant = variants.get(coordinate)
        if variant is None:
            if not payload["create_missing"]:
                raise ValidationError(f"الخلية SPH {row['sphere']} / CYL {row['cylinder']} غير معرّفة. أنشئ المتغير أو اسمح بإنشائه بصلاحية إدارة الكتالوج.")
            specs = {**template.specifications["values"], "sphere": row["sphere"], "cylinder": row["cylinder"]}
            packed, fingerprint = canonical_specs("stock_lens", specs, template.unit)
            variant = Variant(product=product, sku="MX-" + uuid.uuid4().hex.upper(), unit=template.unit,
                base_price=template.base_price, specifications=packed, fingerprint=fingerprint, created_by_id=actor_id, **stock_matrix_fields(packed))
            new = True
        else:
            if not variant.active:
                raise ValidationError("توجد خلية لمتغير موقوف. لا يمكن إضافة رصيد أو إنشاء نسخة بديلة منه.")
            new = False
        balance = balances.get(variant.pk)
        before = balance.on_hand if balance else 0
        if before + row["quantity"] > 9223372036854775807:
            raise ValidationError("الرصيد يتجاوز سعة التخزين.")
        lines.append({**row, "variant": variant, "new": new, "before": before, "after": before + row["quantity"], "reserved": balance.reserved if balance else 0})
    return template, lines


def preview_receipt(actor_id, **values):
    payload = _payload(actor_id, **values)
    template, lines = _plan(actor_id, payload)
    return {"payload": payload, "template": template, "lines": lines, "total": sum(row["quantity"] for row in lines), "new_count": sum(row["new"] for row in lines)}


@transaction.atomic
def receive_matrix(actor_id, **values):
    lock_access()
    payload = _payload(actor_id, **values)
    _require(actor_id, payload)
    fingerprint = digest(payload)
    previous = StockReceipt.objects.filter(operation_key=payload["operation_key"]).first()
    if previous:
        if previous.payload_digest != fingerprint:
            raise ValidationError("مفتاح العملية مستخدم بطلب مختلف. أعد فتح المصفوفة لإضافة جديدة.")
        return previous
    # AccessLock is held: authorization cannot change through access services before commit.
    template, lines = _plan(actor_id, payload, authorized=True)
    new_variants = [line["variant"] for line in lines if line["new"]]
    if new_variants:
        Variant.objects.bulk_create(new_variants)
    document = StockReceipt.objects.create(branch_id=payload["branch_id"], kind="receipt", operation_key=payload["operation_key"],
        payload_digest=fingerprint, reference=payload["reference"], reason=payload["reason"], created_by_id=actor_id)
    ids = [line["variant"].pk for line in lines]
    balances = {b.variant_id: b for b in StockBalance.objects.select_for_update().filter(branch_id=payload["branch_id"], variant_id__in=ids).order_by("variant_id")}
    to_create, to_update, movements = [], [], []
    for line in lines:
        variant = line["variant"]
        balance = balances.get(variant.pk)
        if balance is None:
            balance = StockBalance(branch_id=payload["branch_id"], variant=variant)
            to_create.append(balance)
        else:
            to_update.append(balance)
            balance.version += 1
        before = balance.on_hand
        balance.on_hand += line["quantity"]
        movements.append(StockMovement(receipt=document, branch_id=payload["branch_id"], variant=variant, delta=line["quantity"], before=before, after=balance.on_hand, reserved_after=balance.reserved,
            variant_snapshot={"sku": variant.sku, "product": template.product.name, "unit": variant.unit, "unit_label": template.unit_label, "specifications": variant.specifications}))
    StockBalance.objects.bulk_create(to_create)
    if to_update:
        StockBalance.objects.bulk_update(to_update, ["on_hand", "version"])
    StockMovement.objects.bulk_create(movements)
    audit(actor_id, "stock.received", document.pk)
    return document


@transaction.atomic
def reverse_receipt(actor_id, *, receipt_id, operation_key, reason):
    lock_access()
    document = StockReceipt.objects.select_for_update().get(pk=receipt_id, kind="receipt")
    require(actor_id, "stock.reverse", [document.branch_id])
    require(actor_id, "stock.read", [document.branch_id])
    reason = reason.strip()
    if not reason or len(reason) > 300:
        raise ValidationError("سبب العكس مطلوب حتى300 حرف.")
    try:
        operation_key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError):
        raise ValidationError("مفتاح عملية العكس غير صالح.") from None
    fingerprint = digest({"receipt": str(document.pk), "actor": str(actor_id), "reason": reason})
    previous = StockReceipt.objects.filter(operation_key=operation_key).first()
    if previous:
        if previous.payload_digest != fingerprint:
            raise ValidationError("مفتاح العملية مستخدم بطلب مختلف.")
        return previous
    existing = StockReceipt.objects.filter(reverses=document).first()
    if existing:
        raise ValidationError("عُكست هذه الإضافة مسبقًا. افتح مستند العكس الموجود.")
    entries = list(document.movements.order_by("variant_id"))
    balances = {balance.variant_id: balance for balance in StockBalance.objects.select_for_update().filter(branch_id=document.branch_id, variant_id__in=[e.variant_id for e in entries]).order_by("variant_id")}
    for entry in entries:
        balance = balances.get(entry.variant_id)
        if balance is None or balance.on_hand - entry.delta < balance.reserved:
            raise ValidationError("لا يمكن العكس: بعض الكمية مستخدم أو محجوز. لم يُعدل أي رصيد.")
    reversal = StockReceipt.objects.create(branch=document.branch, kind="reversal", reverses=document, operation_key=operation_key, payload_digest=fingerprint, reason=reason, created_by_id=actor_id)
    movements = []
    for entry in entries:
        balance = balances[entry.variant_id]
        before = balance.on_hand
        balance.on_hand -= entry.delta
        balance.version += 1
        movements.append(StockMovement(receipt=reversal, branch_id=document.branch_id, variant_id=entry.variant_id, delta=-entry.delta, before=before, after=balance.on_hand, reserved_after=balance.reserved, variant_snapshot=entry.variant_snapshot))
    StockBalance.objects.bulk_update(list(balances.values()), ["on_hand", "version"])
    StockMovement.objects.bulk_create(movements)
    audit(actor_id, "stock.receipt_reversed", reversal.pk)
    return reversal
