import hashlib
import json
import unicodedata
import uuid
from decimal import Decimal, localcontext
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from access.authorization import require, current_company, visible_branches
from access.services import lock_access, audit
from catalog.models import Variant
from catalog.services import quote_price
from clinical.models import CustomerBranchAccess
from finance.services import latest_profile
from finance.setup_services import _text, _date
from finance.journal_money import amount
from .models import TaxTreatmentRevision, TaxQuote
from .tax_codes import treatment
from .amounts import calculate_document, UNIT_MAX, _quantity


def require_tax_reader(actor_id):
    require(actor_id, "catalog.read")
    require(actor_id, "ledger.read")


def tax_snapshot(revision):
    return {"id": str(revision.pk), "version": revision.version, "valid_from": revision.valid_from.isoformat(), "state": revision.state,
        "category": revision.category, "rate": format(revision.rate, ".2f") if revision.rate is not None else None,
        "reason_code": revision.reason_code, "reason_text": revision.reason_text, "basis": revision.basis}


def _day(value):
    day = _date(value)
    if day.isoformat() < "2020-07-01":
        raise ValidationError("المسار الحالي يدعم التواريخ منذ2020-07-01، دون افتراض معدل تاريخي سابق.")
    return day


def _request(actor_id, operation_key, reason, **payload):
    reason = _text(reason, 300)
    try:
        key = uuid.UUID(str(operation_key))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("مفتاح العملية غير صالح.") from None
    digest = hashlib.sha256(json.dumps({"company": str(current_company().pk), "actor": str(actor_id), "reason": reason, **payload}, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()
    return key, digest, reason


@transaction.atomic
def revise_treatment(actor_id, *, variant_id, expected_version, valid_from, state, category="", reason_code="", exception_text="", basis, operation_key, reason):
    lock_access()
    require_tax_reader(actor_id)
    require(actor_id, "ledger.post")
    try:
        variant = Variant.objects.get(pk=variant_id)
    except (Variant.DoesNotExist, ValueError, ValidationError):
        raise ValidationError("الصنف غير متاح.") from None
    if isinstance(expected_version, bool) or not isinstance(expected_version, int) or not 0 <= expected_version < 2147483647:
        raise ValidationError("إصدار التصنيف غير صالح.")
    day, basis = _day(valid_from), _text(basis, 500)
    if state == "reviewed":
        tax = treatment(category, reason_code, exception_text)
    elif state == "blocked" and not any((category, reason_code, exception_text)):
        tax = dict(category="", rate=None, reason_code="", reason_text="")
    else:
        raise ValidationError("حدد المراجعة أو الحظر دون تصنيف مفترض للصنف المحظور.")
    key, digest, reason = _request(actor_id, operation_key, reason, kind="tax_revision", variant_id=str(variant.pk), expected_version=expected_version,
        valid_from=day.isoformat(), state=state, tax=tax, basis=basis)
    prior = TaxTreatmentRevision.objects.filter(operation_key=key).first()
    if prior:
        if prior.payload_digest != digest:
            raise ValidationError("مفتاح العملية مستخدم بمحتوى مختلف.")
        return prior
    latest = variant.tax_revisions.order_by("-version").first()
    if expected_version != (latest.version if latest else 0):
        raise ValidationError("تغير التصنيف؛ حدّث الصفحة وراجع آخر إصدار.")
    if latest and day < latest.valid_from:
        raise ValidationError("تاريخ الإصدار الجديد لا يسبق آخر تاريخ بدء؛ لا إعادة كتابة للتاريخ.")
    revision = TaxTreatmentRevision.objects.create(variant=variant, version=expected_version+1, valid_from=day, state=state,
        category=tax["category"], rate=tax["rate"], reason_code=tax["reason_code"], reason_text=tax["reason_text"], basis=basis,
        reason=reason, operation_key=key, payload_digest=digest, created_by_id=actor_id)
    audit(actor_id, "sales.tax.revised", revision.pk)
    return revision


def quotes_for(actor_id):
    require(actor_id, "catalog.read")
    links = CustomerBranchAccess.objects.filter(customer_id=OuterRef("customer_id"), branch_id=OuterRef("branch_id"), customer__active=True)
    return TaxQuote.objects.filter(branch__in=visible_branches(actor_id, "invoice.read")).annotate(customer_visible=Exists(links)).filter(
        Q(customer__isnull=True) | (Q(branch__in=visible_branches(actor_id, "customer.read")) & Q(customer_visible=True)))


def _quote_access(actor_id, branch_id, customer_id):
    require(actor_id, "catalog.read")
    for action in ("invoice.read", "invoice.create"):
        require(actor_id, action, [branch_id])
    if customer_id:
        require(actor_id, "customer.read", [branch_id])
        if not CustomerBranchAccess.objects.filter(customer_id=customer_id, branch_id=branch_id, customer__active=True).exists():
            raise PermissionDenied


def _inputs(lines):
    if not isinstance(lines, list) or not 1 <= len(lines) <= 40:
        raise ValidationError("المعاينة تحتاج1–40 بندًا.")
    result = []
    for row in lines:
        if not isinstance(row, dict) or set(row) != {"sku", "quantity", "price_basis", "unit_amount", "discount_kind", "discount_value"}:
            raise ValidationError("حقول بند المعاينة ناقصة أو غير معروفة.")
        if not isinstance(row["sku"], str) or not 1 <= len(row["sku"].strip()) <= 60:
            raise ValidationError("رمز SKU غير صالح.")
        basis = row["price_basis"]
        if basis not in ("gross", "catalog_net"):
            raise ValidationError("حدد سعرًا نهائيًا أو سعر الكتالوج قبل الضريبة.")
        price = amount(row["unit_amount"]) if basis == "gross" else None
        if basis == "catalog_net" and row["unit_amount"] is not None:
            raise ValidationError("سعر الكتالوج يقرأ من الخادم ولا يقبل مبلغًا بديلًا.")
        if price is not None and price > UNIT_MAX:
            raise ValidationError("سعر الوحدة يتجاوز السعة.")
        value = amount(row["discount_value"])
        if row["discount_kind"] not in ("amount", "percent") or (row["discount_kind"] == "percent" and value > 100):
            raise ValidationError("الخصم مبلغ أو نسبة حتى100%.")
        result.append(dict(sku=unicodedata.normalize("NFKC", row["sku"]).strip().upper(), quantity=_quantity(row["quantity"]), price_basis=basis,
            unit_amount=format(price, ".2f") if price is not None else None, discount_kind=row["discount_kind"], discount_value=format(value, ".2f")))
    return result


@transaction.atomic
def create_tax_quote(actor_id, *, branch_id, as_of, lines, document_discount_kind="amount", document_discount_value="0", customer_id=None, operation_key, reason):
    lock_access()
    _quote_access(actor_id, branch_id, customer_id)
    day, inputs, doc_value = _day(as_of), _inputs(lines), amount(document_discount_value)
    if document_discount_kind not in ("amount", "percent") or (document_discount_kind == "percent" and doc_value > 100):
        raise ValidationError("خصم الإجمالي مبلغ أو نسبة حتى100%.")
    key, digest, reason = _request(actor_id, operation_key, reason, kind="tax_quote", branch_id=str(branch_id), customer_id=str(customer_id) if customer_id else None,
        as_of=day.isoformat(), lines=inputs, document_discount_kind=document_discount_kind, document_discount_value=format(doc_value, ".2f"))
    prior = TaxQuote.objects.filter(operation_key=key).first()
    if prior:
        if prior.payload_digest != digest:
            raise ValidationError("مفتاح العملية مستخدم بمحتوى مختلف.")
        return prior
    profile = latest_profile()
    if profile is None or profile.registration_status == "unknown":
        raise ValidationError("حدد حالة تسجيل المنشأة في الملف الضريبي قبل المعاينة.")
    registered = profile.registration_status == "registered"
    variants = Variant.objects.filter(sku__in={row["sku"] for row in inputs}, active=True, product__active=True).select_related("product").in_bulk(field_name="sku")
    revisions = {item.variant_id: item for item in TaxTreatmentRevision.objects.filter(variant_id__in=[v.pk for v in variants.values()], valid_from__lte=day)
        .order_by("variant_id", "-valid_from", "-version").distinct("variant_id")}
    calculation, sources = [], []
    price_cache = {}
    for row in inputs:
        variant = variants.get(row["sku"])
        if variant is None:
            raise ValidationError("أحد الأصناف غير متاح أو غير نشط.")
        revision = revisions.get(variant.pk)
        tax = None
        if registered:
            if revision is None or revision.state != "reviewed":
                raise ValidationError("أحد الأصناف بلا تصنيف مراجع متاح في تاريخ المعاينة.")
            tax = treatment(revision.category, revision.reason_code, revision.reason_text)
            if tax["rate"] != format(revision.rate, ".2f"):
                raise ValidationError("معدل التصنيف لا يطابق النطاق المدعوم.")
        cache_key = (variant.pk, row["quantity"])
        if cache_key not in price_cache:
            with localcontext() as ctx:
                ctx.prec = 50
                price_cache[cache_key] = quote_price(actor_id, variant_id=variant.pk, branch_id=branch_id, customer_id=customer_id, channel="retail", count=row["quantity"], as_of=day)
        catalog = price_cache[cache_key]
        calculation.append({key: row[key] for key in ("quantity", "price_basis", "discount_kind", "discount_value")} | {
            "unit_amount": row["unit_amount"] if row["price_basis"] == "gross" else catalog["unit_price"], "tax": tax})
        sources.append({"catalog": catalog, "tax_revision": tax_snapshot(revision) if registered else None})
    result = calculate_document(calculation, document_discount_kind=document_discount_kind, document_discount_value=format(doc_value, ".2f"), seller_registered=registered)
    result.update(currency="SAR", as_of=day.isoformat(), customer_id=str(customer_id) if customer_id else None, inputs=inputs,
        document_discount_input={"kind": document_discount_kind, "value": format(doc_value, ".2f")}, sources=sources,
        seller={"profile_id": str(profile.pk), "version": profile.version, "registration_status": profile.registration_status, "legal_name": profile.legal_name, "vat_number": profile.vat_number},
        can_issue_invoice=False, can_submit_to_zatca=False)
    totals = result["totals"]
    quote = TaxQuote.objects.create(branch_id=branch_id, customer_id=customer_id, fiscal_profile=profile, as_of=day, payload=result,
        **{key: Decimal(totals[key]) for key in ("net", "vat", "tax_inclusive", "payable_rounding", "payable")},
        operation_key=key, payload_digest=digest, reason=reason, created_by_id=actor_id)
    audit(actor_id, "sales.tax.quote_created", quote.pk)
    return quote
