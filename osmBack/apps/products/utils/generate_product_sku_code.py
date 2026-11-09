
# def generate_product_sku_code(self):
#     """Helper function to create a unique SKU"""
#     brand_part = str(self.brand_id.id).zfill(3)
#     category_part = str(self.category_id.id).zfill(3)
#     supplier_part = str(self.supplier_id.id).zfill(3)
#     manufacturer_part = str(self.manufacturer_id.id).zfill(3)
#     model_part = self.model.replace(" ", "").upper()
#     return f"{self.type}{brand_part}{category_part}{supplier_part}{manufacturer_part}{model_part}"




import uuid

def generate_sku_code(instance, fields=None, prefix=None):
    """
    دالة ديناميكية لتوليد SKU بناءً على الحقول المطلوبة
    ----------------------------------------------------
    🔹 instance: كائن المنتج أو الـ variant
    🔹 fields: قائمة بأسماء الحقول التي تريد دمجها في الكود
              مثال: ['product.id', 'product.brand_id.id', 'frame_color.id']
    🔹 prefix: اختياري لتحديد بادئة حسب نوع المنتج
    """

    parts = []

    # توليد البادئة من نوع المنتج أو الاسم إن لم تُمرر
    prefix = prefix or getattr(getattr(instance, 'product', None), 'variant_type', 'GEN')
    parts.append(prefix.upper()[:3])

    # المرور على الحقول المرسلة
    for field_path in (fields or []):
        value = instance
        for attr in field_path.split('.'):
            value = getattr(value, attr, None)
            if value is None:
                break
        # إذا القيمة None نضع 000 بدلًا منها
        parts.append(str(value or 0).zfill(3))

    # جزء فريد لضمان عدم التكرار
    parts.append(str(uuid.uuid4().int)[:4])

    return "-".join(parts).upper()


