import hashlib
import json
import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from access.authorization import require, current_company, visible_branches
from access.services import lock_access, audit
from .models import Account, AccountingPeriod, JournalDraft, JournalRevision, JournalEntry, JournalLine, JournalCounter, JournalOperation
from .setup_services import _text, _date, _version, account_snapshot
from .journal_money import normalize_lines, optional_text


def drafts_for(actor_id):
    return JournalDraft.objects.filter(branch__in=visible_branches(actor_id, "ledger.read"))


def entries_for(actor_id):
    return JournalEntry.objects.filter(branch__in=visible_branches(actor_id, "ledger.read"))


def _start(actor_id):
    lock_access()
    require(actor_id, "ledger.read")
    require(actor_id, "ledger.post")


def _branch(actor_id, branch_id):
    require(actor_id, "ledger.read", [branch_id])
    require(actor_id, "ledger.post", [branch_id])


def _draft(actor_id, draft_id):
    try:
        draft = drafts_for(actor_id).select_for_update().get(pk=draft_id)
    except (JournalDraft.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("مسودة القيد غير متاحة.") from None
    _branch(actor_id, draft.branch_id)
    return draft


def _request(actor_id, kind, operation_key, reason, **values):
    reason = _text(reason, 300)
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    fingerprint = hashlib.sha256(json.dumps({"company": str(current_company().pk), "actor": str(actor_id), "kind": kind, "reason": reason, **values}, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    previous = JournalOperation.objects.filter(operation_key=key).first()
    if previous and previous.payload_digest != fingerprint:
        raise ValidationError("مفتاح العملية مستخدم بمحتوى مختلف.")
    return key, fingerprint, reason, previous


def _record(actor_id, kind, request, *, draft=None, entry=None):
    key, fingerprint, reason, _ = request
    result = JournalOperation.objects.create(draft=draft, entry=entry, kind=kind, draft_version=draft.version if draft else None,
        operation_key=key, payload_digest=fingerprint, reason=reason, created_by_id=actor_id)
    audit(actor_id, "finance." + kind, result.pk)
    return result


def _open_period(entry_date):
    period = AccountingPeriod.objects.select_for_update().filter(starts_on__lte=entry_date, ends_on__gte=entry_date).exclude(state="void").first()
    if period is None or period.state != "open":
        raise ValidationError("تاريخ القيد يحتاج فترة مالية مفتوحة غير ملغاة.")
    return period


def _accounts(lines):
    accounts = Account.objects.in_bulk({row["account_code"] for row in lines}, field_name="code")
    if len(accounts) != len({row["account_code"] for row in lines}):
        raise ValidationError("أحد رموز الحسابات غير متاح في الشركة.")
    cache = {account.pk: account for account in accounts.values()}
    for account in accounts.values():
        if account.is_group or not account.active:
            raise ValidationError("كل سطر يحتاج حساب ترحيل نشطًا؛ لا ترحيل على مجموعة.")
        node, visited = account, set()
        while node:
            if node.pk in visited or len(visited) >= 8 or not node.active:
                raise ValidationError("شجرة الحساب غير صالحة أو تتضمن مجموعة معطلة.")
            visited.add(node.pk)
            if not node.parent_id:
                break
            if node.parent_id not in cache:
                cache[node.parent_id] = Account.objects.get(pk=node.parent_id)
            node = cache[node.parent_id]
            if not node.is_group or node.kind != account.kind:
                raise ValidationError("مجموعة الحساب لا تطابق تصنيفه.")
    return accounts


def _contents(entry_date, reference, description, lines):
    day = _date(entry_date)
    reference, description = optional_text(reference, 100), _text(description, 300)
    canonical, debit, credit = normalize_lines(lines)
    return day, reference, description, canonical, debit, credit


def _revision(actor_id, draft, contents):
    day, reference, description, lines, debit, credit = contents
    period = _open_period(day)
    _accounts(lines)
    return JournalRevision.objects.create(draft=draft, version=draft.version, entry_date=day, period=period, reference=reference,
        description=description, lines=lines, total_debit=debit, total_credit=credit, created_by_id=actor_id)


@transaction.atomic
def save_journal_draft(actor_id, *, entry_date, description, lines, operation_key, reason, reference="", branch_id=None, draft_id=None, expected_version=None):
    _start(actor_id)
    draft = _draft(actor_id, draft_id) if draft_id else None
    if draft:
        if branch_id is not None and str(branch_id) != str(draft.branch_id):
            raise ValidationError("فرع القيد ثابت.")
        branch_id = draft.branch_id
        version = _version(expected_version)
    else:
        _branch(actor_id, branch_id)
        if expected_version is not None:
            raise ValidationError("لا إصدار متوقع عند إنشاء مسودة جديدة.")
        version = None
    contents = _contents(entry_date, reference, description, lines)
    day, reference, description, canonical, _, _ = contents
    kind = "draft_revised" if draft else "draft_created"
    request = _request(actor_id, kind, operation_key, reason, branch=branch_id, draft=draft_id, version=version,
        entry_date=day, reference=reference, description=description, lines=canonical)
    if request[3]:
        return request[3]
    if draft:
        if draft.state != "draft" or draft.version != version:
            raise ValidationError("المسودة تغيرت أو لم تعد قابلة للتعديل.")
        draft.version += 1
        draft.save(update_fields=["version"])
    else:
        draft = JournalDraft.objects.create(branch_id=branch_id, created_by_id=actor_id)
    _revision(actor_id, draft, contents)
    return _record(actor_id, kind, request, draft=draft)


def _number():
    counter, _ = JournalCounter.objects.select_for_update().get_or_create(pk=1)
    if counter.next_number > 9223372036854775806:
        raise ValidationError("استنفد تسلسل القيود سعته.")
    number = counter.next_number
    counter.next_number += 1
    counter.save(update_fields=["next_number"])
    return number


def _check_balance():
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS finance_journal_header_balance, finance_journal_line_balance IMMEDIATE")
        cursor.execute("SET CONSTRAINTS finance_journal_header_balance, finance_journal_line_balance DEFERRED")


def _publish(actor_id, *, branch_id, period, entry_date, reference, description, debit, credit, rows, revision=None, reverses=None):
    entry = JournalEntry.objects.create(number=_number(), branch_id=branch_id, period=period, entry_date=entry_date, revision=revision,
        draft_id=revision.draft_id if revision else None, reverses=reverses, reference=reference, description=description,
        total_debit=debit, total_credit=credit, created_by_id=actor_id)
    JournalLine.objects.bulk_create([JournalLine(entry=entry, position=index + 1, **row) for index, row in enumerate(rows)])
    return entry


@transaction.atomic
def act_on_journal_draft(actor_id, *, draft_id, action, expected_version, operation_key, reason):
    _start(actor_id)
    draft = _draft(actor_id, draft_id)
    if not isinstance(action, str) or action not in {"post", "cancel"}:
        raise ValidationError("إجراء المسودة غير صالح.")
    version = _version(expected_version)
    kind = "journal_posted" if action == "post" else "draft_cancelled"
    request = _request(actor_id, kind, operation_key, reason, draft=draft.pk, version=version)
    if request[3]:
        return request[3]
    if draft.state != "draft" or draft.version != version:
        raise ValidationError("المسودة تغيرت أو انتهت؛ لا يمكن تعديل مرحل أو ملغى.")
    entry = None
    if action == "post":
        revision = draft.revisions.order_by("-version").first()
        if revision is None:
            raise ValidationError("لا يوجد إصدار صالح للمسودة.")
        canonical, debit, credit = normalize_lines(revision.lines)
        if debit != revision.total_debit or credit != revision.total_credit or debit != credit or debit <= 0:
            raise ValidationError("لا يرحل القيد إلا إذا تساوى المدين والدائن بمجموع موجب.")
        accounts = _accounts(canonical)
        period = _open_period(revision.entry_date)
        if period.pk != revision.period_id:
            raise ValidationError("الفترة لا تطابق الإصدار المحفوظ.")
        rows = [{"account": accounts[row["account_code"]], "debit": Decimal(row["debit"]), "credit": Decimal(row["credit"]),
            "description": row["description"], "account_snapshot": account_snapshot(accounts[row["account_code"]])} for row in canonical]
        entry = _publish(actor_id, branch_id=draft.branch_id, period=period, entry_date=revision.entry_date, reference=revision.reference,
            description=revision.description, debit=debit, credit=credit, rows=rows, revision=revision)
    draft.state = "posted" if action == "post" else "cancelled"
    draft.version += 1
    draft.save(update_fields=["state", "version"])
    operation = _record(actor_id, kind, request, draft=draft, entry=entry)
    if entry:
        _check_balance()
    return operation


@transaction.atomic
def reverse_journal(actor_id, *, entry_id, entry_date, operation_key, reason):
    _start(actor_id)
    try:
        original = entries_for(actor_id).get(pk=entry_id)
    except (JournalEntry.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("القيد غير متاح.") from None
    _branch(actor_id, original.branch_id)
    day = _date(entry_date)
    if day < original.entry_date:
        raise ValidationError("تاريخ العكس لا يسبق تاريخ القيد الأصلي.")
    request = _request(actor_id, "journal_reversed", operation_key, reason, original=original.pk, entry_date=day)
    if request[3]:
        return request[3]
    if original.reverses_id or JournalEntry.objects.filter(reverses=original).exists():
        raise ValidationError("القيد عكس أو سبق عكسه؛ لا عكس مكرر.")
    period = _open_period(day)
    rows = [{"account_id": row.account_id, "debit": row.credit, "credit": row.debit, "description": row.description, "account_snapshot": row.account_snapshot} for row in original.lines.order_by("position")]
    entry = _publish(actor_id, branch_id=original.branch_id, period=period, entry_date=day, reference=original.reference,
        description=request[2], debit=original.total_credit, credit=original.total_debit, rows=rows, reverses=original)
    operation = _record(actor_id, "journal_reversed", request, entry=entry)
    _check_balance()
    return operation
