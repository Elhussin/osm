"""Custody and immutable counts; payment-derived cash movement is added in M06."""
import hashlib
import json
import uuid
from decimal import localcontext
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, connection
from django.utils import timezone
from access.authorization import require, allowed, current_company, visible_branches
from access.services import lock_access, audit
from finance.setup_services import _text, _version
from finance.journal_money import amount
from .models import CashRegister, CashShift, ShiftEvent
from .registers import _cash_account, register_snapshot


def shifts_for(actor_id):
    return CashShift.objects.filter(branch__in=visible_branches(actor_id, "payment.read"))


def usable_registers(actor_id):
    return CashRegister.objects.filter(active=True, branch__in=visible_branches(actor_id, "payment.record")).filter(branch__in=visible_branches(actor_id, "payment.read"))


def can_supervise(actor_id, branch_id):
    return all(allowed(actor_id, action, [branch_id]) for action in ("payment.read", "payment.record", "payment.reverse"))


def _authorize(actor_id, branch_id):
    for action in ("payment.read", "payment.record"):
        require(actor_id, action, [branch_id])


def _valid_register(register):
    if not register.active:
        raise ValidationError("الصندوق معطل؛ لا يمكن فتح وردية أو نقل عهدة عليه.")
    _cash_account(register.cash_account.code)


def expected_cash(shift):
    # Opening custody is the only cash source until the payment module exists.
    return shift.opening_cash


def shift_snapshot(shift):
    def money(value):
        return format(value, ".2f") if value is not None else None
    return {"id": str(shift.pk), "register_id": str(shift.register_id), "branch_id": str(shift.branch_id),
            "state": shift.state, "version": shift.version, "custodian_id": str(shift.custodian_id),
            "custodian": shift.custodian.username, "pending_to_id": str(shift.pending_to_id) if shift.pending_to_id else None,
            "pending_to": shift.pending_to.username if shift.pending_to_id else None, "pending_cash": money(shift.pending_cash),
            "opening_cash": money(shift.opening_cash), "expected_cash": money(shift.expected_cash),
            "counted_cash": money(shift.counted_cash), "difference": money(shift.difference),
            "closed_at": shift.closed_at.isoformat() if shift.closed_at else None}


def _request(actor_id, kind, operation_key, reason, **values):
    reason = _text(reason, 300)
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    digest = hashlib.sha256(json.dumps({"company": str(current_company().pk), "actor": str(actor_id), "kind": kind, "reason": reason, **values}, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    prior = ShiftEvent.objects.filter(operation_key=key).first()
    if prior and prior.payload_digest != digest:
        raise ValidationError("مفتاح العملية مستخدم بمحتوى مختلف.")
    return key, digest, reason, prior


def _record(actor_id, shift, kind, before, request):
    key, digest, reason, _ = request
    event = ShiftEvent.objects.create(shift=shift, version=shift.version, kind=kind, before=before, after=shift_snapshot(shift),
        operation_key=key, payload_digest=digest, reason=reason, created_by_id=actor_id)
    audit(actor_id, "sales.shift." + kind, shift.pk)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS sales_shift_head_event, sales_shift_event_head IMMEDIATE")
        cursor.execute("SET CONSTRAINTS sales_shift_head_event, sales_shift_event_head DEFERRED")
    return event


@transaction.atomic
def open_shift(actor_id, *, register_id, opening_cash, operation_key, reason):
    lock_access()
    try:
        register = CashRegister.objects.filter(branch__in=visible_branches(actor_id, "payment.read")).select_for_update().select_related("cash_account").get(pk=register_id)
    except (CashRegister.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("الصندوق غير متاح.") from None
    _authorize(actor_id, register.branch_id)
    cash = amount(opening_cash)
    request = _request(actor_id, "opened", operation_key, reason, register_id=str(register.pk), opening_cash=format(cash, ".2f"))
    if request[3]:
        return request[3]
    _valid_register(register)
    if register.shifts.exclude(state="closed").exists():
        raise ValidationError("للصندوق وردية غير مغلقة؛ أكمل إغلاقها أولًا.")
    shift = CashShift.objects.create(register=register, branch_id=register.branch_id, register_snapshot=register_snapshot(register),
        opening_cash=cash, custodian_id=actor_id, created_by_id=actor_id)
    return _record(actor_id, shift, "opened", {}, request)


@transaction.atomic
def act_on_shift(actor_id, *, shift_id, action, expected_version, operation_key, reason, counted_cash=None, recipient_username=None):
    lock_access()
    try:
        shift = shifts_for(actor_id).select_for_update(of=("self",)).select_related("register__cash_account", "custodian", "pending_to").get(pk=shift_id)
    except (CashShift.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("الوردية غير متاحة.") from None
    _authorize(actor_id, shift.branch_id)
    kinds = {"request_handover": "handover_requested", "accept_handover": "handover_accepted", "cancel_handover": "handover_cancelled",
             "reject_handover": "handover_rejected", "submit_count": "count_submitted", "approve_variance": "variance_approved"}
    if not isinstance(action, str) or action not in kinds:
        raise ValidationError("إجراء الوردية غير صالح.")
    if action == "approve_variance":
        require(actor_id, "payment.reverse", [shift.branch_id])
    version = _version(expected_version)
    needs_count = action in {"request_handover", "accept_handover", "submit_count"}
    if not needs_count and counted_cash is not None:
        raise ValidationError("الإجراء لا يقبل تعديل مبلغ الجرد.")
    cash = amount(counted_cash) if needs_count else None
    if action == "request_handover":
        recipient = _text(recipient_username, 150)
    elif recipient_username is not None:
        raise ValidationError("الإجراء لا يقبل تغيير المستلم.")
    else:
        recipient = None
    request = _request(actor_id, kinds[action], operation_key, reason, shift_id=str(shift.pk), version=version,
        counted_cash=format(cash, ".2f") if cash is not None else None, recipient_username=recipient)
    if request[3]:
        return request[3]
    if shift.version != version:
        raise ValidationError("تغيرت الوردية؛ حدّث الصفحة وراجع الحائز والإصدار الحالي.")
    if shift.state == "closed":
        raise ValidationError("الوردية مغلقة ولا يمكن تعديلها أو إعادة فتحها.")
    before = shift_snapshot(shift)
    holder = str(actor_id) == str(shift.custodian_id)
    if action == "approve_variance":
        if shift.state != "review":
            raise ValidationError("لا يوجد فرق جرد معلق للاعتماد.")
        shift.state, shift.closed_at = "closed", timezone.now()
    else:
        if shift.state != "open":
            raise ValidationError("جرد الوردية محفوظ وينتظر اعتماد الفرق؛ لا يعاد تعديله.")
        if action == "request_handover":
            if not holder:
                raise PermissionDenied
            if shift.pending_to_id:
                raise ValidationError("يوجد طلب تسليم معلق بالفعل.")
            _valid_register(shift.register)
            target = get_user_model().objects.filter(username=recipient, is_active=True).first()
            if target is None or target.pk == shift.custodian_id or not all(allowed(target.pk, code, [shift.branch_id]) for code in ("payment.read", "payment.record")):
                raise ValidationError("المستلم غير متاح أو غير مخول في الفرع أو هو الحائز الحالي.")
            if cash != expected_cash(shift):
                raise ValidationError("فرق الجرد يمنع التسليم؛ سجل جرد الإغلاق للمراجعة.")
            shift.pending_to, shift.pending_cash = target, cash
        elif action in {"accept_handover", "cancel_handover", "reject_handover"}:
            if not shift.pending_to_id:
                raise ValidationError("لا يوجد طلب تسليم معلق.")
            if action in {"accept_handover", "reject_handover"}:
                if str(actor_id) != str(shift.pending_to_id):
                    raise PermissionDenied
            elif not holder and not can_supervise(actor_id, shift.branch_id):
                raise PermissionDenied
            if action == "accept_handover":
                _valid_register(shift.register)
                if cash != shift.pending_cash or cash != expected_cash(shift):
                    raise ValidationError("المعدود لا يطابق العهدة المقترحة؛ ارفض الاستلام وراجع الجرد.")
                shift.custodian = shift.pending_to
            shift.pending_to, shift.pending_cash = None, None
        elif action == "submit_count":
            if shift.pending_to_id:
                raise ValidationError("ألغِ أو أكمل التسليم المعلق قبل إغلاق الوردية.")
            if not holder and not can_supervise(actor_id, shift.branch_id):
                raise PermissionDenied
            shift.expected_cash, shift.counted_cash = expected_cash(shift), cash
            with localcontext() as ctx:
                ctx.prec = 40
                shift.difference = cash - shift.expected_cash
            shift.state = "review" if shift.difference else "closed"
            if shift.state == "closed":
                shift.closed_at = timezone.now()
    shift.version += 1
    shift.save(update_fields=["state", "custodian", "pending_to", "pending_cash", "expected_cash", "counted_cash", "difference", "closed_at", "version"])
    return _record(actor_id, shift, kinds[action], before, request)
