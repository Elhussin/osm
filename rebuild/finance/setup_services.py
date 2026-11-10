"""Chart and period configuration. No journal or invoice posting side effects."""
from datetime import date, datetime
import hashlib
import json
import re
import unicodedata
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from access.authorization import require, current_company
from access.services import lock_access, audit
from .models import Account, AccountingPeriod, SetupOperation, JournalRevision, JournalEntry


def _text(value, limit, *, code=False):
    if not isinstance(value, str):
        raise ValidationError("أدخل نصًا صالحًا ضمن الحد المحدد.")
    value = unicodedata.normalize("NFKC", value).strip()
    if code:
        value = value.upper()
    if not value or len(value) > limit or (code and not re.fullmatch(r"[A-Z0-9][A-Z0-9-]*", value)):
        raise ValidationError("الرمز إنجليزي أو رقمي حتى30 حرفًا؛ الاسم مطلوب حتى200 حرف والسبب حتى300 حرف.")
    return value


def _version(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value < 2147483647:
        raise ValidationError("إصدار السجل غير صالح.")
    return value


def _date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError("أدخل تاريخًا صالحًا بالصيغة سنة-شهر-يوم.") from None


def _request(actor_id, *, kind, operation_key, reason, **payload):
    require(actor_id, "ledger.read")
    require(actor_id, "ledger.post")
    reason = _text(reason, 300)
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    fingerprint = hashlib.sha256(json.dumps({"company": str(current_company().pk), "actor": str(actor_id), "kind": kind, "reason": reason, **payload}, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    previous = SetupOperation.objects.filter(operation_key=key).first()
    if previous and previous.payload_digest != fingerprint:
        raise ValidationError("مفتاح العملية مستخدم بطلب مختلف.")
    return key, fingerprint, reason, previous


def _authorize(actor_id):
    lock_access()
    require(actor_id, "ledger.read")
    require(actor_id, "ledger.post")


def _account(account_id):
    try:
        return Account.objects.select_for_update().get(pk=account_id)
    except (Account.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("الحساب غير متاح في الشركة الحالية.") from None


def account_snapshot(account):
    return {field: getattr(account, field) for field in ["code", "name", "kind", "normal_side", "is_group", "path", "depth", "active", "version"]} | {"parent_id": str(account.parent_id) if account.parent_id else None}


def period_snapshot(period):
    return {"code": period.code, "name": period.name, "starts_on": period.starts_on.isoformat(), "ends_on": period.ends_on.isoformat(), "state": period.state, "version": period.version}


def _record(actor_id, kind, target, before, request):
    key, fingerprint, reason, _ = request
    account = isinstance(target, Account)
    operation = SetupOperation.objects.create(account=target if account else None, period=None if account else target, kind=kind,
        before=before, after=account_snapshot(target) if account else period_snapshot(target), operation_key=key, payload_digest=fingerprint, reason=reason, created_by_id=actor_id)
    audit(actor_id, "finance." + kind, operation.pk)
    return operation


@transaction.atomic
def create_account(actor_id, *, code, name, kind, normal_side, is_group, operation_key, reason, parent_id=None):
    _authorize(actor_id)
    code, name = _text(code, 30, code=True), _text(name, 200)
    if not isinstance(kind, str) or kind not in dict(Account.KINDS) or not isinstance(normal_side, str) or normal_side not in dict(Account.SIDES) or type(is_group) is not bool:
        raise ValidationError("حدد تصنيف الحساب وطبيعته ونوعه صراحةً.")
    request = _request(actor_id, kind="account_created", operation_key=operation_key, reason=reason,
        code=code, name=name, account_kind=kind, normal_side=normal_side, is_group=is_group, parent_id=parent_id)
    if request[3]:
        return request[3]
    parent = _account(parent_id) if parent_id else None
    if parent and (not parent.active or not parent.is_group or parent.kind != kind or parent.depth >= 8):
        raise ValidationError("الأب مجموعة نشطة من التصنيف نفسه، والعمق لا يتجاوز8 مستويات.")
    if Account.objects.filter(code=code).exists():
        raise ValidationError("رمز الحساب مسجل؛ لا يمكن إعادة استخدامه.")
    account = Account(code=code, name=name, kind=kind, normal_side=normal_side, is_group=is_group, parent=parent,
        path=(parent.path + "/" if parent else "") + code, depth=parent.depth + 1 if parent else 1, created_by_id=actor_id)
    account.full_clean()
    account.save(force_insert=True)
    return _record(actor_id, "account_created", account, {}, request)


@transaction.atomic
def change_account(actor_id, *, account_id, action, expected_version, operation_key, reason, name=None):
    _authorize(actor_id)
    if not isinstance(action, str) or action not in {"rename", "activate", "disable"} or (action != "rename" and name is not None):
        raise ValidationError("إجراء الحساب غير صالح.")
    version = _version(expected_version)
    name = _text(name, 200) if action == "rename" else None
    kind = {"rename": "account_renamed", "activate": "account_activated", "disable": "account_disabled"}[action]
    request = _request(actor_id, kind=kind, operation_key=operation_key, reason=reason, account_id=account_id, version=version, name=name)
    if request[3]:
        return request[3]
    account = _account(account_id)
    if account.version != version:
        raise ValidationError("تغير الحساب منذ فتح الصفحة؛ راجع الإصدار الحالي.")
    before = account_snapshot(account)
    if action == "rename":
        if name == account.name:
            raise ValidationError("الاسم مطابق للاسم الحالي.")
        account.name = name
    else:
        active = action == "activate"
        if account.active == active:
            raise ValidationError("حالة الحساب مطابقة بالفعل.")
        if not active and account.children.filter(active=True).exists():
            raise ValidationError("عطّل الحسابات الفرعية النشطة أولًا؛ لا تعطيل ضمني للشجرة.")
        if active and account.parent_id and not _account(account.parent_id).active:
            raise ValidationError("فعّل المجموعة الأب أولًا.")
        account.active = active
    account.version += 1
    account.save(update_fields=["name", "active", "version"])
    return _record(actor_id, kind, account, before, request)


@transaction.atomic
def create_period(actor_id, *, code, name, starts_on, ends_on, operation_key, reason):
    _authorize(actor_id)
    code, name = _text(code, 30, code=True), _text(name, 200)
    start, end = _date(starts_on), _date(ends_on)
    if start > end:
        raise ValidationError("بداية الفترة لا تتجاوز نهايتها.")
    request = _request(actor_id, kind="period_created", operation_key=operation_key, reason=reason, code=code, name=name, starts_on=start, ends_on=end)
    if request[3]:
        return request[3]
    if AccountingPeriod.objects.filter(code=code).exists() or AccountingPeriod.objects.filter(starts_on__lte=end, ends_on__gte=start).exclude(state="void").exists():
        raise ValidationError("رمز الفترة مكرر أو تاريخها يتداخل مع فترة محفوظة؛ البداية والنهاية شاملتان.")
    period = AccountingPeriod(code=code, name=name, starts_on=start, ends_on=end, created_by_id=actor_id)
    period.full_clean()
    period.save(force_insert=True)
    return _record(actor_id, "period_created", period, {}, request)


@transaction.atomic
def change_period(actor_id, *, period_id, action, expected_version, operation_key, reason):
    _authorize(actor_id)
    if not isinstance(action, str) or action not in {"close", "reopen", "void"}:
        raise ValidationError("إجراء الفترة غير صالح.")
    version = _version(expected_version)
    kind = {"close": "period_closed", "reopen": "period_reopened", "void": "period_voided"}[action]
    request = _request(actor_id, kind=kind, operation_key=operation_key, reason=reason, period_id=period_id, version=version)
    if request[3]:
        return request[3]
    try:
        period = AccountingPeriod.objects.select_for_update().get(pk=period_id)
    except (AccountingPeriod.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("الفترة غير متاحة في الشركة الحالية.") from None
    state = {"close": "closed", "reopen": "open", "void": "void"}[action]
    if period.version != version:
        raise ValidationError("تغيرت الفترة منذ فتح الصفحة؛ راجع الإصدار الحالي.")
    if period.state == "void":
        raise ValidationError("الفترة ملغاة نهائيًا؛ لا إعادة فتح أو تعديل لها.")
    if action == "void" and (JournalRevision.objects.filter(period=period).exists() or JournalEntry.objects.filter(period=period).exists()):
        raise ValidationError("لا تلغى فترة مرتبطة بأي إصدار قيد، ولو ألغيت المسودة لاحقًا.")
    if period.state == state:
        raise ValidationError("حالة الفترة مطابقة بالفعل.")
    before = period_snapshot(period)
    period.state, period.version = state, period.version + 1
    period.save(update_fields=["state", "version"])
    return _record(actor_id, kind, period, before, request)
