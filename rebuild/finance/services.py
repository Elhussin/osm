import hashlib
import json
import re
import unicodedata
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from access.authorization import require, current_company
from access.services import lock_access, audit
from .models import FiscalProfileRevision

PROFILE_FIELDS = ("legal_name", "registration_status", "vat_number", "commercial_registration", "street", "building_number", "additional_number", "district", "city", "postal_code")


def profile_values(data):
    if set(data) != set(PROFILE_FIELDS):
        raise ValidationError("حقول الملف الضريبي غير مكتملة أو غير معروفة.")
    values = {}
    for name in PROFILE_FIELDS:
        value = data[name]
        if not isinstance(value, str):
            raise ValidationError("بيانات الملف نصوص محددة دون حقول اتصال أو أسرار.")
        # Do not silently convert non-ASCII registration identifiers to ASCII.
        values[name] = value.strip() if name in {"vat_number", "building_number", "additional_number", "postal_code"} else unicodedata.normalize("NFKC", value).strip()
    if values["registration_status"] not in {"unknown", "registered", "not_registered"}:
        raise ValidationError("حدد حالة التسجيل الضريبي.")
    if values["registration_status"] == "registered":
        if not re.fullmatch(r"[0-9]{15}", values["vat_number"]):
            raise ValidationError("رقم ضريبة القيمة المضافة15 رقمًا إنجليزيًا؛ فحص البنية لا يثبت التسجيل لدى الهيئة.")
    elif values["vat_number"]:
        raise ValidationError("رقم VAT يخص حالة مسجل فقط؛ راجع حالة التسجيل.")
    for name, length in (("building_number", 4), ("additional_number", 4), ("postal_code", 5)):
        if values[name] and not re.fullmatch(r"[0-9]{" + str(length) + r"}", values[name]):
            raise ValidationError("رقم المبنى والرقم الإضافي4 أرقام إنجليزية، والرمز البريدي5؛ اترك غير المعروف فارغًا.")
    return values


def latest_profile():
    return FiscalProfileRevision.objects.order_by("-version").first()


@transaction.atomic
def save_fiscal_profile(actor_id, *, data, expected_version, operation_key, reason):
    lock_access()
    require(actor_id, "company.manage")
    if isinstance(expected_version, bool) or not isinstance(expected_version, int) or not 0 <= expected_version < 2147483647:
        raise ValidationError("إصدار الملف غير صالح؛ افتح النموذج من جديد.")
    if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 300:
        raise ValidationError("سبب الإعداد أو التصحيح مطلوب حتى300 حرف.")
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    values = profile_values(data)
    payload = {"company": str(current_company().pk), "actor": str(actor_id), "version": expected_version, "data": values, "reason": reason.strip()}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    previous = FiscalProfileRevision.objects.filter(operation_key=key).first()
    if previous:
        if previous.payload_digest != fingerprint:
            raise ValidationError("مفتاح العملية مستخدم ببيانات مختلفة.")
        return previous
    current = latest_profile()
    if (current.version if current else 0) != expected_version:
        raise ValidationError("تغير الملف منذ فتح النموذج؛ راجع الإصدار الحالي قبل التصحيح.")
    revision = FiscalProfileRevision(version=expected_version + 1, **values, reason=reason.strip(), operation_key=key, payload_digest=fingerprint, created_by_id=actor_id)
    revision.full_clean()
    revision.save(force_insert=True)
    audit(actor_id, "finance.profile_saved", revision.pk)
    return revision
