"""Immediate branch transfers and versioned physical counts; no financial posting."""
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from access.authorization import require, visible_branches
from access.services import lock_access, audit
from .matrix import digest
from .models import StockBalance, StockOperation, StockMovement

MAX_BALANCE = 9223372036854775807


def operations_for(actor_id):
    branches = visible_branches(actor_id, "stock.read")
    return StockOperation.objects.filter(source__in=branches).filter(Q(destination__isnull=True) | Q(destination__in=branches))


def _authorize(actor_id, action, branches):
    require(actor_id, "catalog.read")
    require(actor_id, "stock.read", branches)
    require(actor_id, action, branches)


def _number(value, *, minimum=0, maximum=1000000):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValidationError("الكمية والإصدار أعداد صحيحة ضمن الحدود.")
    try:
        result = int(value)
    except (ValueError, TypeError):
        raise ValidationError("الكمية والإصدار أعداد صحيحة ضمن الحدود.") from None
    if str(result) != str(value) or not minimum <= result <= maximum:
        raise ValidationError("الكمية والإصدار أعداد صحيحة ضمن الحدود.")
    return result


def _request(actor_id, operation_key, reason, reference="", **values):
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 300 or not isinstance(reference, str) or len(reference.strip()) > 100:
        raise ValidationError("السبب مطلوب حتى300 حرف والمرجع اختياري حتى100 حرف.")
    fingerprint = digest({"actor": str(actor_id), "reason": reason.strip(), "reference": reference.strip(), **{k: str(v) for k, v in values.items()}})
    previous = StockOperation.objects.filter(operation_key=key).first()
    if previous and previous.payload_digest != fingerprint:
        raise ValidationError("مفتاح العملية مستخدم بطلب مختلف.")
    return key, fingerprint, reason.strip(), reference.strip(), previous


def _state(balance):
    return {"on_hand": balance.on_hand, "reserved": balance.reserved, "version": balance.version}


def _write(actor_id, *, kind, variant, source_id, destination_id, quantity, key, fingerprint, reason, reference, deltas, balances, reverses=None):
    before = {str(b.branch_id): _state(b) for b in balances.values()}
    entries = []
    snapshot = reverses.variant_snapshot if reverses else {"product": variant.product.name, "sku": variant.sku, "unit": variant.unit,
        "unit_label": variant.unit_label, "specifications": variant.specifications}
    for branch_id, delta in deltas.items():
        balance = balances[branch_id]
        after = balance.on_hand + delta
        if after < balance.reserved:
            raise ValidationError("الكمية المتاحة لا تكفي؛ لا يمكن استهلاك المحجوز أو إنشاء رصيد سالب.")
        if after > MAX_BALANCE:
            raise ValidationError("الرصيد يتجاوز سعة التخزين.")
        if delta:
            entries.append(StockMovement(branch_id=branch_id, variant=variant, before=balance.on_hand, delta=delta, after=after,
                reserved_after=balance.reserved, variant_snapshot=snapshot))
        balance.on_hand = after
        balance.version += 1
    document = StockOperation.objects.create(kind=kind, source_id=source_id, destination_id=destination_id, variant=variant, quantity=quantity,
        operation_key=key, payload_digest=fingerprint, reference=reference, reason=reason, before_values=before,
        after_values={str(b.branch_id): _state(b) for b in balances.values()}, variant_snapshot=snapshot, created_by_id=actor_id, reverses=reverses)
    StockBalance.objects.bulk_update(list(balances.values()), ["on_hand", "version"])
    for entry in entries:
        entry.operation = document
    StockMovement.objects.bulk_create(entries)
    audit(actor_id, "stock.operation_reversed" if reverses else "stock." + kind + "_posted", document.pk)
    return document


@transaction.atomic
def post_operation(actor_id, *, source_balance_id, kind, quantity, expected_version, operation_key, reason, reference="", destination_id=None):
    lock_access()
    if kind not in {"transfer", "count"}:
        raise ValidationError("إجراء غير معروف.")
    source = StockBalance.objects.select_related("variant__product").get(pk=source_balance_id)
    try:
        destination_id = uuid.UUID(str(destination_id)) if destination_id else None
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("معرف الفرع غير صالح.") from None
    branches = [source.branch_id] + ([destination_id] if destination_id else [])
    _authorize(actor_id, "stock.transfer" if kind == "transfer" else "stock.count", branches)
    if (kind == "count" and destination_id is not None) or (kind == "transfer" and (destination_id is None or destination_id == source.branch_id)):
        raise ValidationError("التحويل يحتاج فرعين مختلفين؛ الجرد لفرع واحد.")
    quantity = _number(quantity, minimum=1 if kind == "transfer" else 0)
    version = _number(expected_version, minimum=1, maximum=2147483647)
    key, fingerprint, reason, reference, previous = _request(actor_id, operation_key, reason, reference, kind=kind,
        balance=source.pk, destination=destination_id, quantity=quantity, version=version)
    if previous:
        return previous
    variant = source.variant
    if variant.product.kind != "stock_lens" or not variant.active or not variant.product.active:
        raise ValidationError("العملية متاحة للعدسات المخزنية النشطة فقط.")
    balances = {b.branch_id: b for b in StockBalance.objects.select_for_update().filter(variant=variant, branch_id__in=branches).order_by("branch_id")}
    source = balances[source.branch_id]
    if source.version != version:
        raise ValidationError("تغير الرصيد منذ فتح العملية. حدّث الصفحة وأعد العدّ أو مراجعة التحويل.")
    if kind == "transfer":
        if source.available < quantity:
            raise ValidationError("الكمية المطلوبة تتجاوز المتاح للتحويل.")
        if destination_id not in balances:
            balances[destination_id] = StockBalance.objects.create(variant=variant, branch_id=destination_id)
        deltas = {source.branch_id: -quantity, destination_id: quantity}
    else:
        deltas = {source.branch_id: quantity - source.on_hand}
    return _write(actor_id, kind=kind, variant=variant, source_id=source.branch_id, destination_id=destination_id, quantity=quantity,
        key=key, fingerprint=fingerprint, reason=reason, reference=reference, deltas=deltas, balances=balances)


@transaction.atomic
def reverse_operation(actor_id, *, operation_id, operation_key, reason):
    lock_access()
    original = StockOperation.objects.select_related("variant__product").get(pk=operation_id)
    branches = [original.source_id] + ([original.destination_id] if original.destination_id else [])
    _authorize(actor_id, "stock.reverse", branches)
    if original.kind == "reversal":
        raise ValidationError("لا يمكن عكس مستند عكس؛ أنشئ عملية جديدة مصرحًا بها.")
    key, fingerprint, reason, reference, previous = _request(actor_id, operation_key, reason, kind="reversal", original=original.pk)
    if previous:
        return previous
    if StockOperation.objects.filter(reverses=original).exists():
        raise ValidationError("عُكست هذه العملية مسبقًا.")
    balances = {b.branch_id: b for b in StockBalance.objects.select_for_update().filter(variant_id=original.variant_id, branch_id__in=branches).order_by("branch_id")}
    if original.kind == "count" and balances[original.source_id].version != original.after_values[str(original.source_id)]["version"]:
        raise ValidationError("حدثت عمليات بعد الجرد. نفّذ جردًا جديدًا بدل عكس قراءة قديمة.")
    deltas = {branch: 0 for branch in branches}
    for entry in original.movements.all():
        deltas[entry.branch_id] = -entry.delta
    return _write(actor_id, kind="reversal", variant=original.variant, source_id=original.source_id, destination_id=original.destination_id,
        quantity=original.quantity, key=key, fingerprint=fingerprint, reason=reason, reference=reference, deltas=deltas, balances=balances, reverses=original)
