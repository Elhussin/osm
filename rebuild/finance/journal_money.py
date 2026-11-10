from decimal import Decimal, localcontext
import re
from django.core.exceptions import ValidationError
from .setup_services import _text

MAX_MONEY = Decimal("9999999999999999.99")


def amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValidationError("المبلغ عدد عشري بمنزلتين دون float أو قيمة غير محدودة.")
    if isinstance(value, Decimal):
        if not value.is_finite() or value.as_tuple().exponent < -2 or value < 0 or value > MAX_MONEY:
            raise ValidationError("المبلغ محدود وبمنزلتين كحد أقصى دون تقريب ضمني.")
        value = format(value, "f")
    else:
        if isinstance(value, int) and not 0 <= value <= MAX_MONEY:
            raise ValidationError("المبلغ خارج سعة القيد.")
        value = str(value)
    if len(value) > 19 or not re.fullmatch(r"(?:0|[1-9][0-9]{0,15})(?:\.[0-9]{1,2})?", value):
        raise ValidationError("المبلغ موجب أو صفر وبمنزلتين كحد أقصى ضمن سعة القيد.")
    return Decimal(value)


def optional_text(value, limit):
    if not isinstance(value, str) or len(value.strip()) > limit:
        raise ValidationError("النص الاختياري يتجاوز الحد المسموح.")
    return value.strip()


def normalize_lines(lines):
    if not isinstance(lines, list) or not 2 <= len(lines) <= 40:
        raise ValidationError("القيد يحتاج2–40 سطرًا.")
    result = []
    with localcontext() as ctx:
        ctx.prec = 40
        debit_total = credit_total = Decimal("0.00")
        for row in lines:
            if not isinstance(row, dict) or not {"account_code", "debit", "credit"} <= set(row) or set(row) - {"account_code", "debit", "credit", "description"}:
                raise ValidationError("حقول سطر القيد غير صالحة.")
            debit, credit = amount(row["debit"]), amount(row["credit"])
            if not ((debit > 0 and credit == 0) or (credit > 0 and debit == 0)):
                raise ValidationError("كل سطر مبلغ موجب في المدين أو الدائن فقط.")
            debit_total += debit
            credit_total += credit
            result.append({"account_code": _text(row["account_code"], 30, code=True), "debit": format(debit, ".2f"),
                "credit": format(credit, ".2f"), "description": optional_text(row.get("description", ""), 300)})
        if debit_total > MAX_MONEY or credit_total > MAX_MONEY:
            raise ValidationError("إجمالي القيد يتجاوز سعة التخزين.")
    return result, debit_total, credit_total
