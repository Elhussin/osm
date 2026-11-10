import uuid
from django.core.exceptions import ValidationError
from django.db import transaction, models
from django.utils import timezone
from access.authorization import require, current_company
from access.services import lock_access, audit
from catalog.models import Variant
from catalog.specifications import code
from .models import StockBalance, StockLot, StockPosition, StockReceipt, StockMovement
from .operations import _number
from .matrix import digest
from .tracking import check_stockable, change_position, snapshot, MAX_BALANCE


@transaction.atomic
def receive_stock(actor_id, *, branch_id, variant_id, quantity, operation_key, reason, reference="", lot_code="", expires_on=None, serial=""):
    lock_access()
    require(actor_id, "catalog.read")
    require(actor_id, "stock.read", [branch_id])
    require(actor_id, "stock.receive", [branch_id])
    quantity = _number(quantity, minimum=1)
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 300 or not isinstance(reference, str) or len(reference.strip()) > 100:
        raise ValidationError("السبب مطلوب حتى300 حرف والمرجع اختياري حتى100 حرف.")
    try:
        operation_key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    lot_code = code(lot_code, 80) if lot_code else ""
    serial = code(serial, 80) if serial else ""
    expiry = models.DateField().to_python(expires_on) if expires_on else None
    payload = {"actor": str(actor_id), "company": str(current_company().pk), "branch": str(branch_id), "variant": str(variant_id),
        "quantity": quantity, "lot": lot_code, "expires_on": expiry.isoformat() if expiry else None, "serial": serial,
        "reason": reason.strip(), "reference": reference.strip()}
    fingerprint = digest(payload)
    previous = StockReceipt.objects.filter(operation_key=operation_key).first()
    if previous:
        if previous.payload_digest != fingerprint:
            raise ValidationError("مفتاح العملية مستخدم بطلب مختلف.")
        return previous
    variant = Variant.objects.select_related("product").get(pk=variant_id)
    check_stockable(variant)
    position = None
    if variant.product.kind == "contact_lens":
        if not lot_code or not expiry or serial:
            raise ValidationError("اللاصقة تحتاج رقم دفعة وتاريخ صلاحية، دون رقم تسلسلي.")
        if expiry < timezone.localdate():
            raise ValidationError("لا يمكن استلام دفعة منتهية الصلاحية.")
        lot, _ = StockLot.objects.get_or_create(variant=variant, code=lot_code, defaults={"expires_on": expiry, "created_by_id": actor_id})
        if lot.expires_on != expiry:
            raise ValidationError("تاريخ صلاحية الدفعة محفوظ وثابت؛ لا يمكن تغيير هوية الدفعة.")
        position, _ = StockPosition.objects.select_for_update().get_or_create(variant=variant, branch_id=branch_id, lot=lot, defaults={"created_by_id": actor_id})
    elif variant.product.kind == "device":
        if not serial or lot_code or expiry or quantity != 1:
            raise ValidationError("استلام الجهاز لوحدة واحدة برقم تسلسلي، دون دفعة أو صلاحية.")
        if StockPosition.objects.filter(serial=serial).exists():
            raise ValidationError("الرقم التسلسلي مسجل سابقًا؛ لا يمكن إنشاء وحدة مكررة أو إعادة استخدام هوية خرجت من المخزون.")
        position = StockPosition.objects.create(variant=variant, branch_id=branch_id, serial=serial, created_by_id=actor_id)
    elif lot_code or serial or expiry:
        raise ValidationError("هذا النوع لا يستخدم بيانات دفعة أو رقم تسلسلي.")
    balance, _ = StockBalance.objects.select_for_update().get_or_create(variant=variant, branch_id=branch_id)
    before = balance.on_hand
    if before + quantity > MAX_BALANCE:
        raise ValidationError("الرصيد يتجاوز سعة التخزين.")
    balance.on_hand += quantity
    balance.version += 1
    balance.save(update_fields=["on_hand", "version"])
    change_position(position, delta=quantity)
    document = StockReceipt.objects.create(branch_id=branch_id, kind="receipt", operation_key=operation_key, payload_digest=fingerprint,
        reference=reference.strip(), reason=reason.strip(), created_by_id=actor_id)
    StockMovement.objects.create(receipt=document, variant=variant, branch_id=branch_id, position=position, delta=quantity,
        before=before, after=balance.on_hand, reserved_after=balance.reserved, variant_snapshot=snapshot(variant, position))
    audit(actor_id, "stock.received", document.pk)
    return document
