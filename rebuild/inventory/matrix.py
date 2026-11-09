from decimal import Decimal, InvalidOperation
import hashlib
import json
from django.core.exceptions import ValidationError

MAX_CELLS = 400
STEP = Decimal("0.25")


def power(value, minimum, maximum):
    try:
        if isinstance(value, (float, bool)):
            raise ValueError
        value = Decimal(value)
        if not value.is_finite() or not minimum <= value <= maximum or value % STEP:
            raise ValueError
        return abs(value) if value == 0 else value
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("قوى المصفوفة ضمن الحدود وبخطوة0.25 فقط.") from None


def axes(sphere_min="-2", sphere_max="2", cylinder_min="-2", cylinder_max="0"):
    low_s, high_s = power(sphere_min, -40, 40), power(sphere_max, -40, 40)
    low_c, high_c = power(cylinder_min, -20, 20), power(cylinder_max, -20, 20)
    if low_s > high_s or low_c > high_c:
        raise ValidationError("بداية نطاق القوى لا تتجاوز نهايته.")
    rows, columns = int((high_s - low_s) / STEP) + 1, int((high_c - low_c) / STEP) + 1
    if rows > 41 or columns > 17 or rows * columns > MAX_CELLS:
        raise ValidationError("قلّل النطاق: حد المصفوفة400 خلية، و41 صفًا و17 عمودًا.")
    return [high_s - i * STEP for i in range(rows)], [high_c - i * STEP for i in range(columns)]


def number(value):
    return format(value, ".2f")


def label(value):
    return ("+" if value > 0 else "") + number(value)


def normalize_cells(cells):
    if not isinstance(cells, list) or len(cells) > MAX_CELLS:
        raise ValidationError("عدد الخلايا يتجاوز الحد المسموح.")
    result, seen = [], set()
    for cell in cells:
        try:
            if not isinstance(cell, dict) or set(cell) != {"sphere", "cylinder", "quantity"}:
                raise ValueError
            sph, cyl = power(cell["sphere"], -40, 40), power(cell["cylinder"], -20, 20)
            value = cell["quantity"]
            if isinstance(value, (bool, float)):
                raise ValueError
            quantity = Decimal(value)
            if not quantity.is_finite() or quantity != quantity.to_integral_value() or not 0 <= quantity <= 1000000:
                raise ValueError
            coordinate = (sph, cyl)
            if coordinate in seen:
                raise ValidationError("إحداثيات خلية مكررة في الطلب.")
            seen.add(coordinate)
            if quantity:
                result.append({"sphere": number(sph), "cylinder": number(cyl), "quantity": int(quantity)})
        except (ValueError, TypeError, KeyError, InvalidOperation):
            raise ValidationError("كل كمية عدد صحيح غير سالب حتى1000000. الخلية الفارغة لا تضيف مخزونًا.") from None
    if not result:
        raise ValidationError("أدخل كمية موجبة في خلية واحدة على الأقل.")
    if len({row["sphere"] for row in result}) > 41 or len({row["cylinder"] for row in result}) > 17:
        raise ValidationError("الطلب يتجاوز أبعاد المصفوفة المسموحة.")
    return sorted(result, key=lambda row: (Decimal(row["sphere"]), Decimal(row["cylinder"])))


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
