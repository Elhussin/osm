import uuid
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from .models import FiscalProfileRevision
from .readiness import readiness
from .services import PROFILE_FIELDS, latest_profile, save_fiscal_profile


class FiscalProfileForm(StyledForm):
    legal_name = forms.CharField(label="الاسم القانوني للمنشأة", max_length=200, required=False)
    registration_status = forms.ChoiceField(label="حالة تسجيل ضريبة القيمة المضافة", choices=FiscalProfileRevision._meta.get_field("registration_status").choices)
    vat_number = forms.CharField(label="رقم ضريبة القيمة المضافة", max_length=15, required=False, help_text="للمسجل فقط؛ فحص البنية لا يثبت صحة التسجيل لدى الهيئة.")
    commercial_registration = forms.CharField(label="السجل التجاري", max_length=30, required=False)
    street = forms.CharField(label="الشارع", max_length=200, required=False)
    building_number = forms.CharField(label="رقم المبنى", max_length=4, required=False)
    additional_number = forms.CharField(label="الرقم الإضافي", max_length=4, required=False)
    district = forms.CharField(label="الحي", max_length=100, required=False)
    city = forms.CharField(label="المدينة", max_length=100, required=False)
    postal_code = forms.CharField(label="الرمز البريدي", max_length=5, required=False)
    reason = forms.CharField(label="سبب الإعداد أو التصحيح", max_length=300)
    expected_version = forms.IntegerField(widget=forms.HiddenInput, min_value=0)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


@require_http_methods(["GET", "POST"])
@secured("company.manage")
def fiscal_setup(request):
    current = latest_profile()
    initial = {field: getattr(current, field) for field in PROFILE_FIELDS} if current else {"registration_status": "unknown"}
    initial.update(expected_version=current.version if current else 0, operation_key=uuid.uuid4())
    form = FiscalProfileForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            save_fiscal_profile(request.user.pk, data={field: values[field] for field in PROFILE_FIELDS},
                expected_version=values["expected_version"], operation_key=values["operation_key"], reason=values["reason"])
        except ValidationError as exc:
            # Only expose service-authored messages; model field names aren't product UI.
            form.add_error(None, " ".join(exc.messages) if not hasattr(exc, "error_dict") else "راجع طول البيانات وصحتها قبل حفظ الملف.")
        else:
            messages.success(request, "حُفظ إصدار الملف الضريبي. الربط مع الهيئة غير مفعل.")
            return redirect("fiscal-setup")
    history = FiscalProfileRevision.objects.order_by("-version")
    return page(request, "finance/fiscal_setup.html", title="الملف الضريبي والاستعداد للربط", active_page="fiscal", form=form,
        current=current, readiness=readiness(current), **listing(request, history), status=422 if form.errors else 200)
