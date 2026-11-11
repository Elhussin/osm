"""Pinned ZS06 section 11.2.4 vocabulary, not automatic product classification."""
from django.core.exceptions import ValidationError

CATEGORIES = [("S", "خاضع للمعدل الأساسي 15%"), ("Z", "خاضع لنسبة الصفر"), ("E", "معفى"), ("O", "خارج نطاق الضريبة")]
REASONS = {
    "VATEX-SA-29": ("E", "الخدمات المالية"), "VATEX-SA-29-7": ("E", "عقد تأمين على الحياة"),
    "VATEX-SA-30": ("E", "التوريدات العقارية المعفاة من الضريبة"),
    "VATEX-SA-32": ("Z", "صادرات السلع من المملكة"), "VATEX-SA-33": ("Z", "صادرات الخدمات من المملكة"),
    "VATEX-SA-34-1": ("Z", "النقل الدولي للسلع"), "VATEX-SA-34-2": ("Z", "النقل الدولي للركاب"),
    "VATEX-SA-34-3": ("Z", "الخدمات المرتبطة مباشرة أو عرضياً بتوريد النقل الدولي للركاب"),
    "VATEX-SA-34-4": ("Z", "توريد وسائل النقل المؤهلة"),
    "VATEX-SA-34-5": ("Z", "الخدمات ذات الصلة بنقل السلع أو الركاب، وفقاً للتعريف الوارد بالمادة الخامسة والعشرين من اللائحة التنفيذية لنظام ضريبة القيمة المضافة"),
    "VATEX-SA-35": ("Z", "الأدوية والمعدات الطبية"), "VATEX-SA-36": ("Z", "المعادن المؤهلة"),
    "VATEX-SA-EDU": ("Z", "الخدمات التعليمية الخاصة للمواطنين"),
    "VATEX-SA-HEA": ("Z", "الخدمات الصحية الخاصة للمواطنين"),
    "VATEX-SA-MLTRY": ("Z", "توريد السلع العسكرية المؤهلة"), "VATEX-SA-OOS": ("O", ""),
}
CONTEXT_REQUIRED = {"VATEX-SA-EDU", "VATEX-SA-HEA", "VATEX-SA-MLTRY"}


def treatment(category, reason_code="", exception_text=""):
    if not isinstance(category, str) or category not in dict(CATEGORIES):
        raise ValidationError("التصنيف الضريبي غير محدد أو غير مدعوم.")
    if not isinstance(reason_code, str) or not isinstance(exception_text, str):
        raise ValidationError("سبب المعالجة الضريبية نص محدد.")
    code, text = reason_code.strip(), exception_text.strip()
    if category == "S":
        if code or text:
            raise ValidationError("المعدل الأساسي لا يقبل سبب إعفاء.")
        return {"category": "S", "rate": "15.00", "reason_code": "", "reason_text": ""}
    if code not in REASONS or REASONS[code][0] != category:
        raise ValidationError("رمز السبب لا يطابق الفئة الضريبية.")
    if code in CONTEXT_REQUIRED:
        raise ValidationError("هذا السبب يحتاج سياق مشتري أو معاملة خاصًا؛ لا يعين كتصنيف صنف عام.")
    if category == "O":
        if not text or len(text) > 300:
            raise ValidationError("اكتب سبب الخروج من النطاق حتى300 حرف.")
    elif text and text != REASONS[code][1]:
        raise ValidationError("نص السبب المحدد لا يطابق الرمز الرسمي.")
    else:
        text = REASONS[code][1]
    return {"category": category, "rate": "0.00", "reason_code": code, "reason_text": text}
