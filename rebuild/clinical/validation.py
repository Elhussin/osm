from decimal import Decimal
import re
from django.core.exceptions import ValidationError
from django.utils import timezone

MEASUREMENTS = tuple(f"{eye}_{part}" for eye in ("right", "left") for part in ("sphere", "cylinder", "axis", "add", "pd"))
RANGES = {"sphere": (-40, 40), "cylinder": (-20, 20), "axis": (0, 180), "add": (0, 10), "pd": (0, 100)}


def normalize_digits(value):
    return value.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789"))


def customer_values(values):
    result = {k: values.get(k) for k in ("first_name", "last_name", "identifier", "phone", "email", "date_of_birth")}
    for key in ("first_name", "last_name", "identifier", "phone", "email"):
        result[key] = (result[key] or "").strip()
    result["identifier"] = normalize_digits(result["identifier"]).upper() or None
    phone = re.sub(r"[\s()\-]", "", normalize_digits(result["phone"]))
    if phone and not re.fullmatch(r"\+?[0-9]{7,15}", phone):
        raise ValidationError({"phone": "أدخل رقم هاتف من 7 إلى 15 رقمًا، مع رمز الدولة عند الحاجة."})
    result["phone"] = phone
    if not result["first_name"]:
        raise ValidationError({"first_name": "اسم العميل مطلوب."})
    if result["date_of_birth"] and result["date_of_birth"] > timezone.localdate():
        raise ValidationError({"date_of_birth": "تاريخ الميلاد لا يمكن أن يكون في المستقبل."})
    return result


def validate_measurements(values, has_image=False):
    errors = {}
    for field in MEASUREMENTS:
        value = values.get(field)
        if value is None:
            continue
        part = field.split("_")[1]
        low, high = RANGES[part]
        if isinstance(value, Decimal) and not value.is_finite():
            errors[field] = "أدخل رقمًا صالحًا."
        elif value < low or value > high:
            errors[field] = f"القيمة يجب أن تكون بين {low} و{high}."
        elif part in {"sphere", "cylinder", "add"} and Decimal(value) % Decimal("0.25"):
            errors[field] = "القيمة يجب أن تكون بمضاعفات 0.25."
        elif part == "axis" and int(value) != value:
            errors[field] = "المحور عدد صحيح بين 0 و180."
    for eye in ("right", "left"):
        cylinder, axis = values.get(eye + "_cylinder"), values.get(eye + "_axis")
        if cylinder is not None and cylinder != 0 and axis is None:
            errors[eye + "_axis"] = "المحور مطلوب عند إدخال أسطوانة غير صفرية."
        if axis is not None and cylinder is None:
            errors[eye + "_cylinder"] = "أدخل الأسطوانة المرتبطة بهذا المحور، أو اترك كليهما فارغًا."
    if all(values.get(key) is None for key in MEASUREMENTS) and not has_image:
        errors["__all__"] = "أدخل قياسًا واحدًا على الأقل أو أرفق صورة الفحص للتوثيق."
    if values.get("examined_on") and values["examined_on"] > timezone.localdate():
        errors["examined_on"] = "تاريخ الفحص لا يمكن أن يكون في المستقبل."
    if errors:
        raise ValidationError(errors)
