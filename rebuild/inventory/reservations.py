"""Explicit stock workflow; all writers share AccessLock with receipts and grants."""
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from access.authorization import require, visible_branches
from access.services import lock_access, audit
from .matrix import digest
from .models import StockBalance, StockMovement, StockReservation, ReservationEvent
from .tracking import check_stockable, position_for, snapshot, change_position


def reservations_for(actor_id):
    return StockReservation.objects.filter(branch__in=visible_branches(actor_id, "stock.read"))


def _integer(value, label, *, maximum=1000000):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValidationError(label)
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        raise ValidationError(label) from None
    if str(parsed) != str(value) or not 1 <= parsed <= maximum:
        raise ValidationError(label)
    return parsed


def _request(actor_id, operation_key, reason, **values):
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 300:
        raise ValidationError("سبب العملية مطلوب حتى300 حرف.")
    payload = {"actor": str(actor_id), "reason": reason.strip(), **{k: str(v) for k, v in values.items()}}
    fingerprint = digest(payload)
    previous = ReservationEvent.objects.filter(operation_key=key).first()
    if previous and previous.payload_digest != fingerprint:
        raise ValidationError("مفتاح العملية مستخدم بطلب مختلف.")
    return key, fingerprint, payload["reason"], previous


def _authorize(actor_id, branch_id, action):
    require(actor_id, "catalog.read")
    require(actor_id, "stock.read", [branch_id])
    require(actor_id, action, [branch_id])


def _event(actor_id, reservation, balance, *, kind, quantity, key, fingerprint, reason, reverses=None, delta=0, position=None):
    event = ReservationEvent.objects.create(reservation=reservation, kind=kind, quantity=quantity, version=reservation.version,
        held_after=reservation.held, issued_after=reservation.issued, released_after=reservation.released,
        operation_key=key, payload_digest=fingerprint, reason=reason, created_by_id=actor_id, reverses=reverses)
    before = balance.on_hand
    balance.on_hand += delta
    balance.version += 1
    balance.save(update_fields=["on_hand", "reserved", "version"])
    held_delta = quantity if kind == "reserve" else -quantity if kind in {"issue", "release", "cancel"} else 0
    change_position(position, delta=delta, held_delta=held_delta)
    if delta:
        StockMovement.objects.create(reservation_event=event, branch_id=reservation.branch_id, position=position, variant_id=reservation.variant_id, delta=delta, before=before,
            after=balance.on_hand, reserved_after=balance.reserved, variant_snapshot=reservation.variant_snapshot)
    audit(actor_id, "stock." + kind, event.pk)
    return event


@transaction.atomic
def reserve_stock(actor_id, *, branch_id, variant_id, quantity, operation_key, reason, reference="", position_id=None):
    lock_access()
    _authorize(actor_id, branch_id, "stock.reserve")
    return _reserve_stock(actor_id, branch_id=branch_id, variant_id=variant_id, quantity=quantity, operation_key=operation_key, reason=reason, reference=reference, position_id=position_id)


def _reserve_stock(actor_id, *, branch_id, variant_id, quantity, operation_key, reason, reference="", position_id=None):
    """Private core: caller holds AccessLock and has authorized the owning workflow."""
    quantity = _integer(quantity, "الكمية عدد صحيح موجب حتى1000000.")
    if not isinstance(reference, str) or len(reference.strip()) > 100:
        raise ValidationError("المرجع حتى100 حرف.")
    identity = {"position": str(position_id)} if position_id else {}
    key, fingerprint, reason, previous = _request(actor_id, operation_key, reason, kind="reserve", branch=branch_id,
        variant=variant_id, quantity=quantity, reference=reference.strip(), **identity)
    if previous:
        return previous
    try:
        balance = StockBalance.objects.select_for_update().select_related("variant__product").get(branch_id=branch_id, variant_id=variant_id)
    except StockBalance.DoesNotExist:
        raise ValidationError("لا يوجد رصيد للصنف في الفرع المحدد.") from None
    variant = balance.variant
    check_stockable(variant)
    position = position_for(variant, branch_id, position_id, for_use=True)
    if quantity > balance.available or (position and quantity > position.available):
        raise ValidationError("الكمية المطلوبة تتجاوز المتاح؛ لم يُحجز أي رصيد.")
    reservation = StockReservation.objects.create(branch_id=branch_id, variant=variant, position=position, quantity=quantity, held=quantity,
        reference=reference.strip(), created_by_id=actor_id, variant_snapshot=snapshot(variant, position))
    balance.reserved += quantity
    return _event(actor_id, reservation, balance, kind="reserve", quantity=quantity, key=key, fingerprint=fingerprint, reason=reason, position=position)


@transaction.atomic
def change_reservation(actor_id, *, reservation_id, kind, expected_version, operation_key, reason, quantity=None, issue_id=None):
    lock_access()
    reservation = StockReservation.objects.get(pk=reservation_id)
    _authorize(actor_id, reservation.branch_id, "stock.reverse" if kind == "reverse_issue" else "stock.issue" if kind == "issue" else "stock.reserve")
    from sales.models import OrderHold
    from django.db import connection
    # Migration verification may temporarily run an older inventory schema.
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass(%s)", [connection.schema_name + ".sales_orderhold"])
        has_orders = cursor.fetchone()[0] is not None
    if has_orders and OrderHold.objects.filter(reservation_id=reservation_id).exists():
        raise ValidationError("الحجز مرتبط بطلب بيع؛ استخدم مسار المبيعات.")
    return _change_reservation(actor_id, reservation_id=reservation_id, kind=kind, expected_version=expected_version, operation_key=operation_key, reason=reason, quantity=quantity, issue_id=issue_id)


def _change_reservation(actor_id, *, reservation_id, kind, expected_version, operation_key, reason, quantity=None, issue_id=None):
    """Private core for an already authorized inventory or sales operation."""
    if kind not in ("issue", "release", "cancel", "reverse_issue"):
        raise ValidationError("إجراء غير معروف.")
    reservation = StockReservation.objects.select_for_update().get(pk=reservation_id)
    version = _integer(expected_version, "إصدار الحجز غير صالح.", maximum=2147483647)
    amount = _integer(quantity, "الكمية عدد صحيح موجب حتى1000000.") if kind in {"issue", "release"} else None
    key, fingerprint, reason, previous = _request(actor_id, operation_key, reason, kind=kind, reservation=reservation.pk,
        version=version, quantity=amount, issue_id=issue_id if kind == "reverse_issue" else None)
    if previous:
        return previous
    if reservation.version != version:
        raise ValidationError("تغير الحجز. حدّث الصفحة قبل إجراء عملية جديدة.")
    balance = StockBalance.objects.select_for_update().get(branch_id=reservation.branch_id, variant_id=reservation.variant_id)
    position = position_for(reservation.variant, reservation.branch_id, reservation.position_id, for_use=kind == "issue")
    reverses, delta = None, 0
    if kind == "reverse_issue":
        reverses = ReservationEvent.objects.get(pk=issue_id, reservation=reservation, kind="issue")
        if ReservationEvent.objects.filter(reverses=reverses).exists():
            raise ValidationError("عُكس هذا الصرف مسبقًا.")
        amount = reverses.quantity
        if balance.on_hand + amount > 9223372036854775807:
            raise ValidationError("الرصيد يتجاوز سعة التخزين.")
        reservation.issued -= amount
        reservation.released += amount
        delta = amount
    else:
        if reservation.cancelled:
            raise ValidationError("هذا الحجز ملغى.")
        if kind == "cancel":
            amount = reservation.held
            reservation.cancelled = True
        if amount > reservation.held:
            raise ValidationError("الكمية تتجاوز المتبقي المحجوز.")
        if kind == "issue" and (not reservation.variant.active or not reservation.variant.product.active):
            raise ValidationError("لا يمكن صرف صنف أو متغير موقوف؛ يمكن تحرير الحجز.")
        reservation.held -= amount
        balance.reserved -= amount
        if kind == "issue":
            reservation.issued += amount
            delta = -amount
        else:
            reservation.released += amount
    reservation.version += 1
    reservation.save(update_fields=["held", "issued", "released", "cancelled", "version"])
    return _event(actor_id, reservation, balance, kind=kind, quantity=amount, key=key, fingerprint=fingerprint, reason=reason, reverses=reverses, delta=delta, position=position)
