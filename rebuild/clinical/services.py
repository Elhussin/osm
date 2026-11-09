from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from access.authorization import require, visible_branches, allowed, current_company
from access.services import lock_access, audit
from .models import Customer, CustomerBranchAccess, Prescription, PrescriptionRevision, ExamImage
from .validation import customer_values, validate_measurements, MEASUREMENTS
from .images import normalize_image


def customers_for(actor_id, action="customer.read"):
    return Customer.objects.filter(branch_links__branch__in=visible_branches(actor_id, action)).distinct()


def prescriptions_for(actor_id, action="prescription.read"):
    branches = visible_branches(actor_id, action).filter(pk__in=visible_branches(actor_id, "customer.read"))
    return Prescription.objects.filter(branch__in=branches, customer__branch_links__branch=F("branch")).distinct()


def customer_editable(actor_id, customer):
    branches = tuple(customer.branch_links.values_list("branch_id", flat=True))
    return allowed(actor_id, "customer.write", branches)


@transaction.atomic
def create_customer(actor_id, *, branch_id, **values):
    lock_access()
    require(actor_id, "customer.write", [branch_id])
    customer = Customer(created_by_id=actor_id, **customer_values(values))
    customer.full_clean()
    customer.save()
    CustomerBranchAccess.objects.create(customer=customer, branch_id=branch_id)
    audit(actor_id, "customer.created", customer.pk)
    return customer


@transaction.atomic
def update_customer(actor_id, *, customer_id, expected_version, **values):
    lock_access()
    customer = Customer.objects.select_for_update().get(pk=customer_id)
    branches = tuple(customer.branch_links.values_list("branch_id", flat=True))
    require(actor_id, "customer.write", branches)
    if customer.version != expected_version:
        raise ValidationError("تغير ملف العميل في جلسة أخرى. حدّث الصفحة قبل إعادة الحفظ.")
    for key, value in customer_values(values).items():
        setattr(customer, key, value)
    customer.version += 1
    customer.full_clean()
    customer.save()
    audit(actor_id, "customer.updated", customer.pk)
    return customer


@transaction.atomic
def share_customer(actor_id, *, customer_id, source_branch_id, target_branch_id):
    lock_access()
    require(actor_id, "ownership.transfer")  # Owner-only until a separately tested sharing permission exists.
    require(actor_id, "customer.write", [source_branch_id, target_branch_id])
    customer = Customer.objects.select_for_update().get(pk=customer_id)
    if not CustomerBranchAccess.objects.filter(customer=customer, branch_id=source_branch_id).exists():
        raise PermissionDenied
    _, created = CustomerBranchAccess.objects.get_or_create(customer=customer, branch_id=target_branch_id)
    if created:
        customer.version += 1
        customer.save(update_fields=["version"])
        audit(actor_id, "customer.shared", customer.pk)
    return customer


def _append(actor_id, document, values, image, reason):
    customer = document.customer
    if not customer.active:
        raise ValidationError("العميل غير نشط.")
    # Convert through model fields so direct service callers receive the same validation as HTML.
    revision = PrescriptionRevision(prescription=document, version=document.latest_version + 1,
        created_by_id=actor_id, correction_reason=reason,
        customer_snapshot={"id": str(customer.pk), "name": customer.full_name, "identifier": customer.identifier or ""},
        **{key: values.get(key) for key in (*MEASUREMENTS, "examined_on", "source")},
        examiner=values.get("examiner") or "", notes=values.get("notes") or "")
    revision.examined_on = revision._meta.get_field("examined_on").to_python(revision.examined_on)
    for key in MEASUREMENTS:
        try:
            setattr(revision, key, revision._meta.get_field(key).to_python(getattr(revision, key)))
        except (ValidationError, ValueError, TypeError):
            raise ValidationError({key: "أدخل رقمًا صالحًا."}) from None
    validate_measurements({key: getattr(revision, key) for key in (*MEASUREMENTS, "examined_on")}, has_image=image is not None)
    revision.full_clean()
    revision.save()
    if image is not None:
        ExamImage.objects.create(revision=revision, **image)
    document.latest_version = revision.version
    document.save(update_fields=["latest_version"])
    audit(actor_id, "prescription.corrected" if revision.version > 1 else "prescription.created", revision.pk)
    return revision


def record_prescription(actor_id, *, customer_id, branch_id, image=None, **values):
    # Reject unauthorized requests before decoding an image; recheck under the access lock below.
    require(actor_id, "prescription.write", [branch_id])
    normalized = normalize_image(image)
    with transaction.atomic():
        lock_access()
        require(actor_id, "prescription.write", [branch_id])
        require(actor_id, "customer.read", [branch_id])
        customer = Customer.objects.select_for_update().get(pk=customer_id)
        if not customer.branch_links.filter(branch_id=branch_id).exists():
            raise PermissionDenied
        document = Prescription.objects.create(customer=customer, branch_id=branch_id, created_by_id=actor_id)
        return _append(actor_id, document, values, normalized, "")


def correct_prescription(actor_id, *, prescription_id, expected_version, correction_reason, image=None, image_action="keep", **values):
    document = prescriptions_for(actor_id, "prescription.write").get(pk=prescription_id)
    if not correction_reason.strip():
        raise ValidationError({"correction_reason": "سبب التصحيح مطلوب لحفظ التاريخ."})
    if image_action not in {"keep", "replace", "remove"} or (image is not None and image_action != "replace"):
        raise ValidationError({"image_action": "حدد الإبقاء أو الاستبدال أو الإزالة من الإصدار الجديد."})
    if image_action == "replace" and image is None:
        raise ValidationError({"image": "أرفق الصورة البديلة."})
    normalized = normalize_image(image)
    with transaction.atomic():
        lock_access()
        require(actor_id, "prescription.write", [document.branch_id])
        require(actor_id, "customer.read", [document.branch_id])
        document = Prescription.objects.select_for_update().select_related("customer").get(pk=prescription_id)
        if document.latest_version != expected_version:
            raise ValidationError("يوجد إصدار أحدث من الفحص. حدّث الصفحة قبل التصحيح.")
        if not document.customer.branch_links.filter(branch_id=document.branch_id).exists():
            raise PermissionDenied
        if image_action == "keep":
            previous = ExamImage.objects.filter(revision__prescription=document, revision__version=document.latest_version).first()
            if previous:
                normalized = {key: getattr(previous, key) for key in ("data", "sha256", "width", "height")}
        return _append(actor_id, document, values, normalized, correction_reason.strip())


def prescription_snapshot(actor_id, *, prescription_id, version):
    document = prescriptions_for(actor_id).get(pk=prescription_id)
    revision = document.revisions.get(version=version)
    return {"company_id": str(current_company().pk), "prescription_id": str(document.pk), "revision_id": str(revision.pk),
        "documentation_only": all(getattr(revision, key) is None for key in MEASUREMENTS),
        "version": revision.version, "branch_id": str(document.branch_id), "customer": revision.customer_snapshot.copy(),
        "examined_on": revision.examined_on.isoformat(),
        **{key: str(getattr(revision, key)) if getattr(revision, key) is not None else None for key in MEASUREMENTS}}
