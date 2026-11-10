"""Stock identity primitives; callers hold AccessLock and an atomic transaction."""
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import StockPosition

PLAIN_KINDS = frozenset({"stock_lens", "frame", "accessory"})
TRACKED_KINDS = frozenset({"contact_lens", "device"})
STOCK_KINDS = PLAIN_KINDS | TRACKED_KINDS
MAX_BALANCE = 9223372036854775807


def check_stockable(variant, *, active=True):
    if variant.product.kind not in STOCK_KINDS or (active and (not variant.active or not variant.product.active)):
        raise ValidationError("يلزم صنف مخزني نشط؛ الخدمة وعدسات التصنيع خارج أرصدة المخزون.")


def usable(position):
    if position and position.lot_id and position.lot.expires_on < timezone.localdate():
        raise ValidationError("انتهت صلاحية الدفعة؛ لا يمكن حجزها أو صرفها. يمكن جردها أو نقلها أو عكس أثر سابق.")


def position_for(variant, branch_id, position_id, *, for_use=False):
    if variant.product.kind in TRACKED_KINDS:
        if not position_id:
            raise ValidationError("حدد دفعة اللاصقة أو الوحدة التسلسلية صراحةً.")
        try:
            position = StockPosition.objects.select_for_update(of=("self",)).select_related("lot").get(pk=position_id, variant=variant, branch_id=branch_id)
        except StockPosition.DoesNotExist:
            raise ValidationError("هوية المخزون غير متاحة للصنف والفرع المحددين.") from None
        if (variant.product.kind == "contact_lens") != bool(position.lot_id) or (position.lot_id and position.lot.variant_id != variant.pk):
            raise ValidationError("هوية التتبع لا تطابق نوع الصنف.")
        if for_use:
            usable(position)
        return position
    if position_id:
        raise ValidationError("هذا الصنف لا يستخدم دفعة أو رقمًا تسلسليًا.")
    return None


def snapshot(variant, position=None):
    result = {"sku": variant.sku, "product": variant.product.name, "unit": variant.unit, "unit_label": variant.unit_label, "specifications": variant.specifications}
    if position:
        result["tracking"] = {"lot": position.lot.code, "expires_on": position.lot.expires_on.isoformat()} if position.lot_id else {"serial": position.serial}
    return result


def change_position(position, *, delta=0, held_delta=0):
    if position is None:
        return
    on_hand, reserved = position.on_hand + delta, position.reserved + held_delta
    if not 0 <= reserved <= on_hand <= MAX_BALANCE or (position.serial and on_hand > 1):
        raise ValidationError("رصيد الدفعة أو الوحدة لا يكفي، أو تتجاوز الكمية حدود التتبع.")
    position.on_hand, position.reserved = on_hand, reserved
    position.version += 1
    position.save(update_fields=["on_hand", "reserved", "version"])


def operation_positions(variant, source_id, destination_id, position_id, *, actor_id, reverse=False):
    if not position_id:
        position_for(variant, source_id, None)
        return {}
    try:
        identity = StockPosition.objects.get(pk=position_id)
    except StockPosition.DoesNotExist:
        raise ValidationError("هوية المخزون غير متاحة.") from None
    expected_branch = destination_id if reverse and destination_id and identity.serial else source_id
    position = position_for(variant, expected_branch, position_id)
    if position.serial:
        return {branch: position for branch in [source_id, destination_id] if branch}
    positions = {source_id: position}
    if destination_id:
        if reverse:
            destination = StockPosition.objects.select_for_update().get(variant=variant, branch_id=destination_id, lot=position.lot)
        else:
            destination, _ = StockPosition.objects.select_for_update().get_or_create(variant=variant, branch_id=destination_id, lot=position.lot,
                defaults={"created_by_id": actor_id})
        positions[destination_id] = destination
    return positions


def position_state(position, branch_id):
    if position.branch_id != branch_id:
        return {"id": str(position.pk), "on_hand": 0, "reserved": 0, "version": position.version}
    return {"id": str(position.pk), "on_hand": position.on_hand, "reserved": position.reserved, "version": position.version}


def apply_operation_positions(positions, deltas):
    if not positions:
        return
    first = next(iter(positions.values()))
    if first.serial and len(deltas) == 2:
        source = next(branch for branch, delta in deltas.items() if delta < 0)
        destination = next(branch for branch, delta in deltas.items() if delta > 0)
        if first.branch_id != source or first.on_hand != 1 or first.reserved or deltas[source] != -1 or deltas[destination] != 1:
            raise ValidationError("التحويل يتطلب الوحدة التسلسلية الموجودة وغير المحجوزة في المصدر.")
        first.branch_id = destination
        first.version += 1
        first.save(update_fields=["branch", "version"])
    else:
        for branch_id, delta in deltas.items():
            change_position(positions[branch_id], delta=delta)
