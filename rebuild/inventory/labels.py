import base64
from decimal import Decimal
import re
from xml.etree import ElementTree as ET
from barcode import Code128
from barcode.writer import SVGWriter
from django.core.exceptions import ValidationError
from django.db.models import Q
from access.authorization import require
from catalog.models import Variant

LAYOUTS = {"standard": {"capacity": 12, "width": Decimal("84"), "title": "A4 عمودي · 90×43 ملم"},
           "wide": {"capacity": 4, "width": Decimal("264"), "title": "A4 أفقي · 270×43 ملم"}}


def compact_specs(variant):
    values = variant.specifications["values"]
    kind = variant.product.kind
    if kind in {"stock_lens", "contact_lens"}:
        parts = [f"SPH: {values['sphere']}", f"CYL: {values['cylinder']}"]
        if kind == "contact_lens":
            parts += [f"AXIS: {values['axis']}"] if "axis" in values else []
            parts += [f"ADD: {values['add']}", f"BC: {values['base_curve']}", f"PACK: {values['pack_size']}"]
        else:
            parts += [values["material"], values["index"], ", ".join(values.get("coatings", []))]
    elif kind == "frame":
        parts = [values["color"], f"{values['eye_size']} / {values['bridge']} / {values['temple']}"]
    elif kind == "device":
        parts = [values["specification"]]
    else:
        parts = [values.get("color", ""), values.get("size", "")]
    return " · ".join(str(part) for part in parts if part != "")


def barcode_image(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z0-9][A-Z0-9._/\-]{0,79}", value):
        raise ValidationError("قيمة الباركود غير صالحة للطباعة.")
    svg = Code128(value, writer=SVGWriter()).render({"module_width": 0.25, "module_height": 12,
        "quiet_zone": 6.5, "write_text": False})
    # Serialize the trusted library output without its external SVG DTD.
    root = ET.fromstring(svg)
    width = Decimal(root.attrib["width"].removesuffix("mm"))
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return {"uri": "data:image/svg+xml;base64," + base64.b64encode(ET.tostring(root, encoding="utf-8")).decode("ascii"), "width": width}


def label_preview(actor_id, *, variant_id, copies, layout="auto"):
    require(actor_id, "catalog.read")
    if isinstance(copies, bool) or not isinstance(copies, (int, str)):
        raise ValidationError("عدد الملصقات عدد صحيح من1 إلى120.")
    try:
        count = int(copies)
    except (TypeError, ValueError):
        raise ValidationError("عدد الملصقات عدد صحيح من1 إلى120.") from None
    if str(count) != str(copies) or not 1 <= count <= 120 or not isinstance(layout, str) or layout not in {"auto", *LAYOUTS}:
        raise ValidationError("عدد الملصقات أو قالب الطباعة غير صالح.")
    variant = Variant.objects.select_related("product").get(pk=variant_id, active=True, product__active=True,
        product__kind__in=["frame", "stock_lens", "contact_lens", "accessory", "device"])
    value = variant.barcode or variant.sku
    if Variant.objects.filter(Q(sku=value) | Q(barcode=value)).exclude(pk=variant.pk).exists():
        raise ValidationError("قيمة الرمز تطابق SKU أو باركود لمتغير آخر. يلزم حل تعارض الهوية قبل الطباعة.")
    image = barcode_image(value)
    if layout == "auto":
        layout = "standard" if image["width"] <= LAYOUTS["standard"]["width"] else "wide"
    preset = LAYOUTS[layout]
    if image["width"] > preset["width"]:
        raise ValidationError("الرمز أطول من عرض الملصق. اختر القالب العريض؛ لن تُقص القيمة أو تُضغط الخطوط.")
    specs = compact_specs(variant)
    capacity = preset["capacity"]
    return {"variant": variant, "code_value": value, "code_source": "الباركود المسجل" if variant.barcode else "SKU ثابت لعدم وجود باركود مسجل",
        "image_uri": image["uri"], "layout": layout, "layout_title": preset["title"], "copies": count,
        "specs": specs, "sheets": [range(min(capacity, count-start)) for start in range(0, count, capacity)]}
