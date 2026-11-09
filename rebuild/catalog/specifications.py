"""Explicit optical variant schemas; no attribute names taken from user-defined database rows."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
import unicodedata
from django.core.exceptions import ValidationError


@dataclass(frozen=True)
class Spec:
    label: str
    type: str = "text"
    required: bool = False
    minimum: str = "0"
    maximum: str = "200"
    step: str = "0.01"
    choices: tuple = ()


LENS = {
    "material": Spec("مادة العدسة", required=True),
    "index": Spec("معامل الانكسار", "decimal", True, "1", "2.5"),
    "diameter": Spec("قطر العدسة (ملم)", "decimal", True, "1", "100"),
    "design": Spec("تصميم العدسة", "choice", True, choices=(("single", "أحادية البؤرة"), ("bifocal", "ثنائية البؤرة"), ("progressive", "متدرجة"))),
    "color": Spec("لون العدسة"),
    "coatings": Spec("الطلاءات (افصل بفاصلة)", "tokens"),
}
POWERS = {"sphere": Spec("SPH", "decimal", True, "-40", "40", "0.25"), "cylinder": Spec("CYL", "decimal", False, "-20", "20", "0.25")}
SCHEMAS = {
    "frame": {"color": Spec("لون الإطار", required=True), "eye_size": Spec("عرض العدسة (ملم)", "integer", True, "20", "100"), "bridge": Spec("عرض الجسر (ملم)", "integer", True, "1", "40"), "temple": Spec("طول الذراع (ملم)", "integer", True, "50", "200"), "material": Spec("مادة الإطار"), "shape": Spec("شكل الإطار")},
    "stock_lens": {**LENS, **POWERS},
    "rx_lens": dict(LENS),
    "contact_lens": {"material": Spec("مادة العدسة", required=True), "diameter": Spec("قطر العدسة (ملم)", "decimal", True, "10", "20"), "base_curve": Spec("المنحنى الأساسي BC", "decimal", True, "5", "12"), **POWERS, "axis": Spec("AXIS", "integer", False, "0", "180"), "add": Spec("ADD", "decimal", False, "0", "10", "0.25"), "color": Spec("لون العدسة"), "pack_size": Spec("عدد العدسات في العلبة", "integer", True, "1", "180"), "replacement": Spec("دورية الاستبدال", "choice", True, choices=(("daily", "يومية"), ("biweekly", "كل أسبوعين"), ("monthly", "شهرية"), ("yearly", "سنوية"), ("other", "أخرى"))), "water_content": Spec("نسبة الماء %", "decimal", False, "0", "100")},
    "accessory": {"color": Spec("اللون"), "size": Spec("المقاس / الوصف")},
    "device": {"specification": Spec("المواصفة / الإصدار", required=True)},
    "service": {"description": Spec("وصف الخدمة", required=True)},
}


def text(value):
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).split()).casefold()


def code(value, length=60):
    value = unicodedata.normalize("NFKC", str(value or "")).strip().upper()
    if not value or len(value) > length or not re.fullmatch(r"[A-Z0-9][A-Z0-9._/\-]*", value):
        raise ValidationError("استخدم رمزًا من أحرف إنجليزية وأرقام وشرطة أو نقطة أو /، دون مسافات.")
    return value


def money(value):
    try:
        if isinstance(value, (float, bool)):
            raise ValueError
        amount = Decimal(value)
        if not amount.is_finite() or amount < 0 or amount > Decimal("9999999999.99") or amount.as_tuple().exponent < -2:
            raise ValueError
        return amount.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("أدخل سعرًا غير سالب بدقة منزلتين عشريتين كحد أقصى.") from None


def canonical_specs(kind, values, unit):
    if kind not in SCHEMAS or not isinstance(values, dict):
        raise ValidationError("نوع المنتج أو مواصفاته غير صالحة.")
    allowed_units = ("piece", "pair") if kind in {"stock_lens", "rx_lens"} else (("box",) if kind == "contact_lens" else (("service",) if kind == "service" else ("piece",)))
    if unit not in allowed_units:
        raise ValidationError({"unit": "وحدة البيع غير مناسبة لهذا النوع."})
    if set(values) - set(SCHEMAS[kind]):
        raise ValidationError("توجد مواصفات غير معتمدة لهذا النوع.")
    result, errors = {}, {}
    for key, spec in SCHEMAS[kind].items():
        value = values.get(key)
        if value is None or value == "":
            if key in {"cylinder", "add"}:
                value = "0"
            elif spec.required:
                errors[key] = "هذا الحقل مطلوب."
                continue
            else:
                result[key] = [] if spec.type == "tokens" else None
                continue
        try:
            if spec.type in {"integer", "decimal"}:
                if isinstance(value, (float, bool)):
                    raise ValueError
                number = Decimal(value)
                if not number.is_finite() or not Decimal(spec.minimum) <= number <= Decimal(spec.maximum) or number % Decimal("1" if spec.type == "integer" else spec.step):
                    raise ValueError
                if number == 0:
                    number = abs(number)
                result[key] = int(number) if spec.type == "integer" else format(number.quantize(Decimal("0.01")), "f")
            elif spec.type == "choice":
                if value not in dict(spec.choices):
                    raise ValueError
                result[key] = value
            elif spec.type == "tokens":
                items = re.split(r"[,،\n]", value) if isinstance(value, str) else value
                if not isinstance(items, (list, tuple)) or len(items) > 20:
                    raise ValueError
                if any(not isinstance(item, str) for item in items):
                    raise ValueError
                result[key] = sorted({text(item) for item in items if text(item)})
                if any(len(item) > 50 for item in result[key]):
                    raise ValueError
            else:
                if not isinstance(value, str):
                    raise ValueError
                result[key] = text(value)
                if not result[key] or len(result[key]) > 100:
                    raise ValueError
        except (ValueError, TypeError, InvalidOperation):
            errors[key] = "تحقق من القيمة وحدودها وخطوتها المحددة."
    if kind == "contact_lens" and "cylinder" in result:
        cylinder = Decimal(result["cylinder"])
        if cylinder and result.get("axis") is None:
            errors["axis"] = "محور العدسة اللاصقة مطلوب للأسطوانة غير الصفرية."
        if not cylinder and result.get("axis") is not None:
            errors["axis"] = "اترك المحور فارغًا عندما تكون الأسطوانة صفرًا."
    if errors:
        raise ValidationError(errors)
    packed = {"schema": 1, "kind": kind, "unit": unit, "values": result}
    fingerprint = hashlib.sha256(json.dumps(packed, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return packed, fingerprint


def display_specs(variant):
    schema = SCHEMAS[variant.product.kind]
    values = variant.specifications["values"]
    return [(spec.label, ", ".join(values[key]) if isinstance(values[key], list) else (dict(spec.choices).get(values[key], values[key]) if spec.choices else values[key])) for key, spec in schema.items() if values.get(key) is not None and values[key] != []]


def stock_matrix_fields(packed):
    if packed["kind"] != "stock_lens":
        return {"matrix_family": None, "sphere": None, "cylinder": None}
    values = {key: value for key, value in packed["values"].items() if key not in {"sphere", "cylinder"}}
    family = {**packed, "values": values}
    digest = hashlib.sha256(json.dumps(family, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return {"matrix_family": digest, "sphere": Decimal(packed["values"]["sphere"]), "cylinder": Decimal(packed["values"]["cylinder"])}
