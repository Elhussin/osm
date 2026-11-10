ROLE_LABELS = {
    "owner": "مالك الشركة", "company_admin": "مسؤول الشركة", "catalog_reader": "قارئ دليل المنتجات",
    "accountant": "المحاسب", "integration_admin": "مسؤول الربط", "branch_manager": "مدير الفرع",
    "cashier": "موظف المبيعات", "optometrist": "أخصائي البصريات", "inventory_clerk": "مسؤول المخزون", "insurance_officer": "مسؤول التأمين",
}
ACTION_LABELS = {
    "stock.count": "اعتماد جرد المخزون",
    "stock.receive": "إضافة مخزون", "stock.issue": "صرف مخزون محجوز", "stock.reverse": "عكس حركة مخزون",
    "company.manage": "إدارة بيانات الشركة", "members.manage": "إدارة الأعضاء", "roles.manage": "إسناد الأدوار",
    "branches.manage": "إدارة الفروع", "ownership.transfer": "نقل ملكية الشركة", "provider.configure": "إعداد الربط الخارجي",
    "catalog.read": "عرض دليل المنتجات", "catalog.manage": "إدارة دليل المنتجات", "ledger.read": "عرض دفتر الأستاذ", "ledger.post": "ترحيل القيود", "audit.read": "عرض سجل التدقيق",
    "customer.read": "عرض العملاء", "customer.write": "تعديل العملاء", "prescription.read": "عرض الوصفات", "prescription.write": "تسجيل الوصفات",
    "invoice.read": "عرض الفواتير", "invoice.create": "إنشاء الفواتير", "invoice.confirm": "اعتماد الفواتير", "payment.read": "عرض الدفعات", "payment.record": "تسجيل الدفعات", "payment.reverse": "عكس الدفعات",
    "stock.read": "عرض المخزون", "stock.reserve": "حجز المخزون", "stock.transfer": "تحويل المخزون", "insurance.read": "عرض ملفات التأمين", "insurance.prepare": "إعداد طلبات التأمين", "insurance.submit": "إرسال طلبات التأمين", "reports.read": "عرض التقارير", "data.export": "تصدير البيانات",
}
EVENT_LABELS = {
    "finance.profile_saved": "حفظ إصدار الملف الضريبي",
    "stock.transfer_posted": "تحويل مخزون بين الفروع", "stock.count_posted": "اعتماد جرد مخزون", "stock.operation_reversed": "عكس تحويل أو جرد",
    "stock.reserve": "حجز مخزون", "stock.issue": "صرف مخزون محجوز", "stock.release": "تحرير حجز مخزون", "stock.cancel": "إلغاء المتبقي من حجز", "stock.reverse_issue": "عكس صرف مخزون",
    "stock.received": "استلام مخزون", "stock.receipt_reversed": "عكس إضافة مخزون",
    "catalog.product_created": "إضافة منتج", "catalog.product_updated": "تحديث منتج", "catalog.variant_created": "إضافة متغير", "catalog.variant_updated": "تحديث سعر متغير", "catalog.price_rule_created": "إضافة قاعدة سعر", "catalog.price_rule_disabled": "إيقاف قاعدة سعر",
    "customer.created": "إضافة عميل", "customer.updated": "تحديث بيانات عميل", "customer.shared": "مشاركة بيانات عميل", "prescription.created": "تسجيل فحص ووصفة", "prescription.corrected": "تصحيح وصفة بإصدار جديد", "prescription.image_viewed": "عرض صورة فحص",
    "company.provisioned": "إنشاء الشركة", "branch.created": "إضافة فرع", "branch.updated": "تحديث فرع", "branch.disabled": "إيقاف فرع", "branch.activated": "تفعيل فرع",
    "member.created": "إضافة عضو", "member.invited": "دعوة عضو", "member.updated": "تحديث عضو", "member.activated": "تفعيل عضو", "member.disabled": "إيقاف عضو",
    "role.assigned": "إسناد دور", "role.revoked": "سحب دور", "branch_access.granted": "منح وصول لفرع", "branch_access.revoked": "سحب وصول لفرع",
    "ownership.transferred": "نقل الملكية", "session.login": "تسجيل الدخول", "session.logout": "تسجيل الخروج", "password_link.issued": "إصدار رابط آمن", "password_link.consumed": "استخدام رابط آمن",
    "invitation.email_queued": "جدولة بريد الدعوة", "invitation.email_sent": "إرسال رابط بالبريد", "invitation.email_failed": "تعذّر إرسال البريد", "provider.configured": "إعداد الربط الخارجي",
}
