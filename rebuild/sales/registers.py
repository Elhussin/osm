"""Register configuration only. No payments, shift cash or journal posting."""
import hashlib
import json
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from access.authorization import require, current_company, visible_branches
from access.services import lock_access, audit
from finance.models import Account
from finance.setup_services import _text, _version, account_snapshot
from .models import CashRegister, RegisterOperation


def require_register_admin(actor_id):
    for action in ("company.manage", "ledger.read", "ledger.post"):
        require(actor_id, action)


def registers_for(actor_id):
    require_register_admin(actor_id)
    return CashRegister.objects.filter(branch__in=visible_branches(actor_id, "payment.read"))


def _start(actor_id, branch_id):
    lock_access()
    require_register_admin(actor_id)
    require(actor_id, "payment.read", [branch_id])


def _request(actor_id, kind, operation_key, reason, **payload):
    reason = _text(reason, 300)
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    digest = hashlib.sha256(json.dumps({"company": str(current_company().pk), "actor": str(actor_id), "kind": kind, "reason": reason, **payload}, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    previous = RegisterOperation.objects.filter(operation_key=key).first()
    if previous and previous.payload_digest != digest:
        raise ValidationError("مفتاح العملية مستخدم بمحتوى مختلف.")
    return key, digest, reason, previous


def _cash_account(code):
    account = Account.objects.filter(code=code).first()
    if account is None or account.kind != "asset" or account.normal_side != "debit" or account.is_group or not account.active:
        raise ValidationError("اختر حساب نقدية نشطًا من الأصول، بطبيعة مدينة ومن نوع حساب ترحيل.")
    node, visited = account, set()
    while node:
        if node.pk in visited or len(visited) >= 8 or not node.active or node.kind != "asset":
            raise ValidationError("شجرة حساب النقدية غير صالحة أو تتضمن مجموعة معطلة.")
        visited.add(node.pk)
        if not node.parent_id:
            break
        node = Account.objects.filter(pk=node.parent_id, is_group=True).first()
        if node is None:
            raise ValidationError("المجموعة الأب غير متاحة.")
    return account


def register_snapshot(register):
    return {"id": str(register.pk), "branch_id": str(register.branch_id), "code": register.code, "name": register.name,
            "cash_account_id": str(register.cash_account_id), "cash_account": account_snapshot(register.cash_account),
            "currency": register.currency, "active": register.active, "version": register.version}


def _record(actor_id, register, kind, before, request):
    key, digest, reason, _ = request
    operation = RegisterOperation.objects.create(register=register, kind=kind, before=before, after=register_snapshot(register),
        reason=reason, operation_key=key, payload_digest=digest, created_by_id=actor_id)
    audit(actor_id, "sales.register." + kind, register.pk)
    return operation


@transaction.atomic
def create_register(actor_id, *, branch_id, code, name, cash_account_code, operation_key, reason):
    _start(actor_id, branch_id)
    code, name, cash_code = _text(code, 30, code=True), _text(name, 200), _text(cash_account_code, 30, code=True)
    request = _request(actor_id, "created", operation_key, reason, branch_id=str(branch_id), code=code, name=name, cash_account_code=cash_code)
    if request[3]:
        return request[3]
    account = _cash_account(cash_code)
    if CashRegister.objects.filter(branch_id=branch_id, code=code).exists():
        raise ValidationError("رمز الصندوق مستخدم في هذا الفرع.")
    if CashRegister.objects.filter(cash_account=account).exists():
        raise ValidationError("حساب النقدية مخصص لصندوق آخر؛ اختر حسابًا مستقلًا.")
    register = CashRegister.objects.create(branch_id=branch_id, code=code, name=name, cash_account=account, created_by_id=actor_id)
    return _record(actor_id, register, "created", {}, request)


@transaction.atomic
def change_register(actor_id, *, register_id, action, expected_version, operation_key, reason, name=None):
    lock_access()
    require_register_admin(actor_id)
    try:
        register = registers_for(actor_id).select_for_update().select_related("cash_account").get(pk=register_id)
    except (CashRegister.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("الصندوق غير متاح.") from None
    require(actor_id, "payment.read", [register.branch_id])
    if not isinstance(action, str) or action not in {"rename", "activate", "disable"} or (action != "rename" and name is not None):
        raise ValidationError("إجراء الصندوق غير صالح.")
    version = _version(expected_version)
    name = _text(name, 200) if action == "rename" else None
    kind = {"rename": "renamed", "activate": "activated", "disable": "disabled"}[action]
    request = _request(actor_id, kind, operation_key, reason, register_id=str(register.pk), version=version, name=name)
    if request[3]:
        return request[3]
    if register.version != version:
        raise ValidationError("تغير إعداد الصندوق؛ حدّث الصفحة وراجع الإصدار الحالي.")
    before = register_snapshot(register)
    if action == "rename":
        if register.name == name:
            raise ValidationError("اسم الصندوق مطابق بالفعل.")
        register.name = name
    else:
        active = action == "activate"
        if register.active == active:
            raise ValidationError("حالة الصندوق مطابقة بالفعل.")
        if active:
            _cash_account(register.cash_account.code)
        register.active = active
    register.version += 1
    register.save(update_fields=["name", "active", "version"])
    return _record(actor_id, register, kind, before, request)
