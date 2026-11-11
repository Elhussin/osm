"""Atomic order lifecycle. No invoicing, issue, payment or journal posting."""
import uuid
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from access.authorization import require, visible_branches
from access.services import lock_access, audit
from clinical.models import Customer, CustomerBranchAccess, PrescriptionRevision, ExamImage
from clinical.services import prescription_snapshot
from inventory.reservations import _reserve_stock, _change_reservation
from inventory.models import ReservationEvent
from inventory.tracking import STOCK_KINDS, position_for
from catalog.models import Variant
from .models import SaleOrder, OrderRevision, OrderEvent, OrderHold, CashShift, TaxQuote
from .taxes import _request, quotes_for, create_tax_quote
from .shifts import _valid_register


def orders_for(actor_id):
    require(actor_id, "catalog.read")
    links = CustomerBranchAccess.objects.filter(customer_id=OuterRef("customer_id"), branch_id=OuterRef("branch_id"))
    medical = OrderRevision.objects.filter(order_id=OuterRef("pk"), prescription_revision__isnull=False)
    return SaleOrder.objects.filter(branch__in=visible_branches(actor_id, "invoice.read")).filter(branch__in=visible_branches(actor_id, "customer.read")).annotate(
        customer_visible=Exists(links), medical=Exists(medical)).filter(customer_visible=True).filter(Q(medical=False) | Q(branch__in=visible_branches(actor_id, "prescription.read")))


def _read(actor_id, order_id):
    try:
        return orders_for(actor_id).select_for_update(of=("self",)).select_related("customer", "current_revision__quote", "current_revision__prescription_revision").get(pk=order_id)
    except (SaleOrder.DoesNotExist, ValueError, ValidationError):
        raise PermissionDenied from None


def _shift(actor_id, shift_id, branch_id):
    for action in ("payment.read", "payment.record"):
        require(actor_id, action, [branch_id])
    shift = CashShift.objects.select_related("register__cash_account").filter(pk=shift_id, branch_id=branch_id, state="open", custodian_id=actor_id, pending_to__isnull=True).first()
    if shift is None:
        raise ValidationError("يلزم وردية مفتوحة بعهدتك في الفرع، دون تسليم معلق.")
    _valid_register(shift.register)
    return shift


def _customer(customer):
    return {key: (getattr(customer, key).isoformat() if key == "date_of_birth" and customer.date_of_birth else getattr(customer, key)) for key in (
        "first_name", "last_name", "identifier", "phone", "email", "date_of_birth", "version")}


def _clinical(actor_id, branch_id, customer_id, revision_id):
    if revision_id is None:
        return None, None
    require(actor_id, "prescription.read", [branch_id])
    revision = PrescriptionRevision.objects.select_related("prescription").filter(pk=revision_id, prescription__branch_id=branch_id, prescription__customer_id=customer_id).first()
    if revision is None:
        raise PermissionDenied
    if revision.version != revision.prescription.latest_version:
        raise ValidationError("صحح الفحص منذ اختياره؛ اختر أحدث إصدار وراجع المسودة.")
    snap = prescription_snapshot(actor_id, prescription_id=revision.prescription_id, version=revision.version)
    image = ExamImage.objects.filter(revision=revision).values("sha256", "width", "height").first()
    snap["image"] = ({"revision_id": str(revision.pk), **image} if image else None)
    return revision, snap


def _positions(actor_id, quote, positions):
    if not isinstance(positions, list) or len(positions) != len(quote.payload["rows"]):
        raise ValidationError("يلزم اختيار تتبع مقابل كل بند، أو تركه فارغًا للصنف العادي.")
    result = []
    for source, value in zip(quote.payload["sources"], positions):
        if value in (None, ""):
            value = None
        else:
            try:
                value = str(uuid.UUID(str(value)))
            except (ValueError, TypeError, AttributeError):
                raise ValidationError("هوية التتبع غير صالحة.") from None
        variant = Variant.objects.select_related("product").get(pk=source["catalog"]["variant_id"])
        if variant.product.kind in STOCK_KINDS:
            position_for(variant, quote.branch_id, value, for_use=True)
        elif value is not None:
            raise ValidationError("الصنف غير المخزني لا يقبل هوية مخزون.")
        result.append(value)
    return result


def _event(actor_id, order, kind, request):
    key, digest, reason = request
    event = OrderEvent.objects.create(order=order, version=order.version, kind=kind, operation_key=key, payload_digest=digest, reason=reason, created_by_id=actor_id)
    audit(actor_id, "sales.order." + kind, order.pk)
    return event


def _prior(request):
    key, digest, _ = request
    previous = OrderEvent.objects.filter(operation_key=key).first()
    if previous and previous.payload_digest != digest:
        raise ValidationError("مفتاح العملية مستخدم بمحتوى مختلف.")
    return previous


@transaction.atomic
def save_order(actor_id, *, quote_id, shift_id, prescription_revision_id=None, positions, operation_key, reason, order_id=None, expected_version=0):
    lock_access()
    try:
        quote = quotes_for(actor_id).select_related("customer").get(pk=quote_id)
    except (TaxQuote.DoesNotExist, ValueError, ValidationError):
        raise PermissionDenied from None
    require(actor_id, "invoice.create", [quote.branch_id])
    require(actor_id, "customer.read", [quote.branch_id])
    if quote.customer_id is None:
        raise ValidationError("اختر معاينة مرتبطة بعميل لإنشاء طلب البيع.")
    order = _read(actor_id, order_id) if order_id else None
    if order and (order.branch_id != quote.branch_id or order.customer_id != quote.customer_id or str(order.shift_id) != str(shift_id)):
        raise ValidationError("العميل والفرع والوردية ثابتة؛ أنشئ طلبًا مستقلًا.")
    if isinstance(expected_version, bool) or not isinstance(expected_version, int) or not 0 <= expected_version < 2147483647:
        raise ValidationError("إصدار الطلب غير صالح.")
    if prescription_revision_id:
        require(actor_id, "prescription.read", [quote.branch_id])
    request = _request(actor_id, operation_key, reason, kind="save_order", order_id=str(order_id) if order_id else None, quote_id=str(quote.pk),
        shift_id=str(shift_id), prescription_revision_id=str(prescription_revision_id) if prescription_revision_id else None, positions=positions, expected_version=expected_version)
    previous = _prior(request)
    if previous:
        # Recheck current data access before returning an old result.
        _read(actor_id, previous.order_id)
        return previous
    if (order and (order.state != "draft" or order.version != expected_version)) or (not order and expected_version != 0):
        raise ValidationError("تغير الطلب أو لم يعد مسودة؛ حدّث الصفحة.")
    if OrderRevision.objects.filter(quote=quote).exists() or SaleOrder.objects.filter(confirmed_quote=quote).exists():
        raise ValidationError("هذه المعاينة مرتبطة بطلب؛ أنشئ معاينة جديدة للتعديل.")
    if quote.as_of != timezone.localdate() or not quote.customer.active:
        raise ValidationError("يلزم عميل نشط ومعاينة بتاريخ اليوم.")
    _shift(actor_id, shift_id, quote.branch_id)
    prescription, clinical = _clinical(actor_id, quote.branch_id, quote.customer_id, prescription_revision_id)
    variants = Variant.objects.filter(pk__in=[s["catalog"]["variant_id"] for s in quote.payload["sources"]]).select_related("product")
    if any(v.product.kind == "rx_lens" for v in variants) and (clinical is None or clinical["documentation_only"]):
        raise ValidationError("عدسة التصنيع تحتاج وصفة بقياسات فعلية؛ الصورة اختيارية.")
    positions = _positions(actor_id, quote, positions)
    if order:
        order.version += 1
    else:
        order = SaleOrder.objects.create(branch_id=quote.branch_id, customer=quote.customer, shift_id=shift_id, created_by_id=actor_id)
    revision = OrderRevision.objects.create(order=order, version=order.version, quote=quote, prescription_revision=prescription,
        positions=positions, snapshot={"customer": _customer(quote.customer), "prescription": clinical})
    order.current_revision = revision
    order.save(update_fields=["version", "current_revision"])
    return _event(actor_id, order, "saved", request)


@transaction.atomic
def act_on_order(actor_id, *, order_id, action, expected_version, operation_key, reason):
    lock_access()
    order = _read(actor_id, order_id)
    require(actor_id, "invoice.confirm", [order.branch_id])
    if action not in ("confirm", "cancel") or isinstance(expected_version, bool) or not isinstance(expected_version, int) or expected_version < 1:
        raise ValidationError("الإجراء أو الإصدار غير صالح.")
    request = _request(actor_id, operation_key, reason, kind="order_" + action, order_id=str(order.pk), expected_version=expected_version)
    previous = _prior(request)
    if previous:
        return previous
    if order.version != expected_version or order.state == "cancelled" or (action == "confirm" and order.state != "draft"):
        raise ValidationError("تغير الطلب أو انتهى؛ حدّث الصفحة.")
    revision = order.current_revision
    if action == "confirm":
        _shift(actor_id, order.shift_id, order.branch_id)
        if not order.customer.active or revision.snapshot["customer"] != _customer(order.customer):
            raise ValidationError("تغير العميل؛ راجع مسودة جديدة.")
        if revision.quote.as_of != timezone.localdate():
            raise ValidationError("أعد المعاينة بتاريخ اليوم.")
        _clinical(actor_id, order.branch_id, order.customer_id, revision.prescription_revision_id)
        payload = revision.quote.payload
        probe_key = uuid.uuid5(request[0], "confirmed-quote")
        # A new order operation must calculate now, never replay a separately
        # preclaimed quote/stock key. Completed order replays returned above.
        if TaxQuote.objects.filter(operation_key=probe_key).exists():
            raise ValidationError("مفتاح تابع مستخدم خارج عملية التأكيد؛ أعد الطلب بمفتاح جديد.")
        quote = create_tax_quote(actor_id, branch_id=order.branch_id, customer_id=order.customer_id, as_of=payload["as_of"], lines=payload["inputs"],
            document_discount_kind=payload["document_discount_input"]["kind"], document_discount_value=payload["document_discount_input"]["value"],
            operation_key=probe_key, reason=reason)
        if quote.payload != payload:
            raise ValidationError("تغير السعر أو التصنيف أو ملف البائع؛ راجع معاينة جديدة قبل التأكيد.")
        for index, source in enumerate(payload["sources"]):
            variant = Variant.objects.select_related("product").get(pk=source["catalog"]["variant_id"])
            if variant.product.kind in STOCK_KINDS:
                hold_key = uuid.uuid5(request[0], "hold-" + str(index))
                if ReservationEvent.objects.filter(operation_key=hold_key).exists():
                    raise ValidationError("مفتاح حجز تابع مستخدم خارج التأكيد؛ لا يمكن تبني حجز سابق.")
                event = _reserve_stock(actor_id, branch_id=order.branch_id, variant_id=variant.pk, quantity=payload["rows"][index]["quantity"],
                    position_id=revision.positions[index], operation_key=hold_key, reason=reason, reference="SALE-" + str(order.pk))
                OrderHold.objects.create(revision=revision, position=index+1, reservation=event.reservation)
        order.confirmed_quote = quote
        order.state = "confirmed"
    else:
        for hold in revision.holds.select_related("reservation").order_by("position"):
            reservation = hold.reservation
            if reservation.issued or reservation.released or reservation.cancelled or reservation.held != reservation.quantity:
                raise ValidationError("تغير الحجز أو صرف منه؛ يلزم مسار تسوية مرتبط بالأصل.")
            _change_reservation(actor_id, reservation_id=reservation.pk, kind="cancel", expected_version=reservation.version,
                operation_key=uuid.uuid5(request[0], "release-" + str(hold.position)), reason=reason)
        order.state = "cancelled"
    order.version += 1
    order.save(update_fields=["version", "state", "confirmed_quote"])
    return _event(actor_id, order, "confirmed" if action == "confirm" else "cancelled", request)
