from dataclasses import dataclass


@dataclass(frozen=True)
class Readiness:
    seller_data_complete: bool
    missing_fields: tuple[str, ...]
    registration_verified: bool = False
    can_issue_tax_invoice: bool = False
    can_submit_to_zatca: bool = False


REQUIRED = {"legal_name": "الاسم القانوني", "commercial_registration": "السجل التجاري", "street": "الشارع", "building_number": "رقم المبنى", "additional_number": "الرقم الإضافي", "district": "الحي", "city": "المدينة", "postal_code": "الرمز البريدي"}


def readiness(profile):
    """Local setup checklist, not validation of a taxpayer or a ZATCA document."""
    missing = [label for field, label in REQUIRED.items() if profile is None or not getattr(profile, field)]
    if profile is None or profile.registration_status == "unknown":
        missing.append("تحديد حالة تسجيل ضريبة القيمة المضافة")
    if profile is not None and profile.registration_status == "registered" and not profile.vat_number:
        missing.append("رقم ضريبة القيمة المضافة")
    return Readiness(not missing, tuple(missing))
