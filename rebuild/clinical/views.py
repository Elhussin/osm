from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q, F
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from access.authorization import require, allowed, visible_branches
from access.services import audit
from workspace.views import secured, page, listing
from . import services
from .models import Customer, PrescriptionRevision, ExamImage
from .forms import CustomerForm, NewCustomerForm, ShareForm, PrescriptionForm
from .validation import normalize_digits, MEASUREMENTS


def attempt(form, operation):
    try:
        return operation()
    except ValidationError as exc:
        if hasattr(exc, "message_dict"):
            for key, errors in exc.message_dict.items():
                if any(getattr(error, "code", None) == "unique" for error in exc.error_dict.get(key, [])):
                    errors = ["تعذّر استخدام هذه البيانات. راجع رقم الوثيقة مع مسؤول مخول."]
                form.add_error(key if key in form.fields else None, errors)
        else:
            form.add_error(None, exc)
    except IntegrityError:
        form.add_error(None, "تعذّر الحفظ بسبب تعارض البيانات. حدّث الصفحة وتحقق من رقم الوثيقة.")
    return None


@require_http_methods(["GET"])
@secured()
def customers(request):
    rows = services.customers_for(request.user.pk).order_by("first_name", "last_name", "id")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        normalized = normalize_digits(q)
        rows = rows.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=normalized) | Q(identifier__icontains=normalized))
    return page(request, "clinical/customers.html", title="العملاء", active_page="customers", can_create=visible_branches(request.user.pk, "customer.write").exists(), **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured()
def customer_new(request):
    branches = visible_branches(request.user.pk, "customer.write")
    if not branches.exists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    initial = {"branch_id": request.session.get("selected_branch")} if request.method == "GET" else None
    form = NewCustomerForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        branch = data.pop("branch_id")
        data.pop("expected_version", None)
        customer = attempt(form, lambda: services.create_customer(request.user.pk, branch_id=branch.pk, **data))
        if customer:
            messages.success(request, "أُضيف ملف العميل.")
            return redirect("customer-detail", customer_id=customer.pk)
    return page(request, "clinical/customer_form.html", title="إضافة عميل", active_page="customers", form=form, status=422 if form.errors else 200)


@require_http_methods(["GET"])
@secured()
def customer_detail(request, customer_id):
    customer = get_object_or_404(services.customers_for(request.user.pk), pk=customer_id)
    revisions = PrescriptionRevision.objects.filter(prescription__in=services.prescriptions_for(request.user.pk), prescription__customer=customer, version=F("prescription__latest_version")).select_related("prescription__branch").order_by("-examined_on", "-created_at")
    can_write = visible_branches(request.user.pk, "prescription.write").filter(customerbranchaccess__customer=customer).exists()
    return page(request, "clinical/customer_detail.html", title=customer.full_name, active_page="customers", customer=customer,
        editable=services.customer_editable(request.user.pk, customer), can_record=can_write,
        can_share=allowed(request.user.pk, "ownership.transfer"), **listing(request, revisions))


@require_http_methods(["GET", "POST"])
@secured()
def customer_edit(request, customer_id):
    customer = get_object_or_404(services.customers_for(request.user.pk), pk=customer_id)
    require(request.user.pk, "customer.write", tuple(customer.branch_links.values_list("branch_id", flat=True)))
    initial = {key: getattr(customer, key) for key in ("first_name", "last_name", "identifier", "phone", "email", "date_of_birth")}
    initial["expected_version"] = customer.version
    form = CustomerForm(request.POST if request.method == "POST" else None, initial=initial)
    form.fields["expected_version"].required = True
    if request.method == "POST" and form.is_valid():
        result = attempt(form, lambda: services.update_customer(request.user.pk, customer_id=customer.pk, **form.cleaned_data))
        if result:
            messages.success(request, "حُفظت بيانات العميل.")
            return redirect("customer-detail", customer_id=customer.pk)
    return page(request, "clinical/customer_form.html", title="تعديل بيانات العميل", active_page="customers", form=form, customer=customer, status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured("ownership.transfer")
def customer_share(request, customer_id):
    customer = get_object_or_404(services.customers_for(request.user.pk), pk=customer_id)
    form = ShareForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, customer=customer)
    if request.method == "POST" and form.is_valid():
        result = attempt(form, lambda: services.share_customer(request.user.pk, customer_id=customer.pk, source_branch_id=form.cleaned_data["source_branch_id"].pk, target_branch_id=form.cleaned_data["target_branch_id"].pk))
        if result:
            messages.success(request, "شُوركت بيانات العميل دون مشاركة فحوص الفروع الأخرى.")
            return redirect("customer-detail", customer_id=customer.pk)
    return page(request, "clinical/customer_form.html", title="مشاركة بيانات العميل مع فرع", active_page="customers", form=form, customer=customer, sharing=True, status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured()
def prescription_new(request, customer_id):
    customer = get_object_or_404(services.customers_for(request.user.pk), pk=customer_id)
    branches = visible_branches(request.user.pk, "prescription.write").filter(customerbranchaccess__customer=customer)
    if not branches.exists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = PrescriptionForm(request.POST if request.method == "POST" else None, request.FILES if request.method == "POST" else None,
        actor_id=request.user.pk, customer=customer, initial={"examined_on": timezone.localdate(), "source": "internal", "branch_id": branches.first().pk})
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        branch = data.pop("branch_id")
        data.pop("expected_version", None)
        revision = attempt(form, lambda: services.record_prescription(request.user.pk, customer_id=customer.pk, branch_id=branch.pk, **data))
        if revision:
            messages.success(request, "حُفظ الفحص والوصفة.")
            return redirect("prescription-detail", prescription_id=revision.prescription_id, version=revision.version)
    return page(request, "clinical/prescription_form.html", title="تسجيل فحص ووصفة", active_page="customers", form=form, customer=customer, status=422 if form.errors else 200)


@require_http_methods(["GET"])
@secured()
def prescription_detail(request, prescription_id, version):
    document = get_object_or_404(services.prescriptions_for(request.user.pk), pk=prescription_id)
    revision = get_object_or_404(document.revisions.select_related("created_by"), version=version)
    pairs = [(label, getattr(revision, "right_" + part), getattr(revision, "left_" + part)) for part, label in (("sphere", "SPH"), ("cylinder", "CYL"), ("axis", "AXIS"), ("add", "ADD"), ("pd", "PD"))]
    return page(request, "clinical/prescription_detail.html", title="تفاصيل الفحص والوصفة", active_page="customers", document=document, revision=revision,
        documentation_only=all(getattr(revision, key) is None for key in MEASUREMENTS),
        measurements=pairs, history=document.revisions.order_by("-version"), has_image=ExamImage.objects.filter(revision=revision).exists(),
        can_correct=allowed(request.user.pk, "prescription.write", [document.branch_id]))


@require_http_methods(["GET", "POST"])
@secured()
def prescription_correct(request, prescription_id):
    document = get_object_or_404(services.prescriptions_for(request.user.pk, "prescription.write"), pk=prescription_id)
    latest = document.revisions.get(version=document.latest_version)
    previous_image = ExamImage.objects.filter(revision=latest).exists()
    initial = {key: getattr(latest, key) for key in (*MEASUREMENTS, "examined_on", "source", "examiner", "notes")}
    initial.update(expected_version=latest.version, image_action="keep")
    form = PrescriptionForm(request.POST if request.method == "POST" else None, request.FILES if request.method == "POST" else None,
        actor_id=request.user.pk, customer=document.customer, correction=True, previous_image=previous_image, initial=initial)
    if request.method == "POST" and form.is_valid():
        revision = attempt(form, lambda: services.correct_prescription(request.user.pk, prescription_id=document.pk, **form.cleaned_data))
        if revision:
            messages.success(request, "حُفظ إصدار مصحح مع إبقاء الإصدار السابق.")
            return redirect("prescription-detail", prescription_id=document.pk, version=revision.version)
    return page(request, "clinical/prescription_form.html", title="تصحيح الفحص بإصدار جديد", active_page="customers", form=form, customer=document.customer, correction=True, status=422 if form.errors else 200)


@require_http_methods(["GET"])
@secured()
def exam_image(request, prescription_id, version):
    document = get_object_or_404(services.prescriptions_for(request.user.pk), pk=prescription_id)
    image = get_object_or_404(ExamImage, revision__prescription=document, revision__version=version)
    audit(request.user.pk, "prescription.image_viewed", image.revision_id)
    response = HttpResponse(bytes(image.data), content_type="image/png")
    response["Content-Disposition"] = 'inline; filename="eye-exam.png"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
    response["Cross-Origin-Resource-Policy"] = "same-origin"
    return response
