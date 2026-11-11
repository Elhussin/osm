import uuid
from django import forms
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from access.models import Branch
from access.authorization import visible_branches
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from finance.setup_views import attempt
from .registers import require_register_admin, registers_for, create_register, change_register


class RegisterForm(StyledForm):
    branch_id = forms.ModelChoiceField(label="فرع الصندوق", queryset=Branch.objects.none())
    code = forms.CharField(label="رمز الصندوق", max_length=30)
    name = forms.CharField(label="اسم الصندوق", max_length=200)
    cash_account_code = forms.CharField(label="رمز حساب النقدية", max_length=30, help_text="حساب ترحيل مستقل من الأصول بطبيعة مدينة، مخصص لهذا الصندوق.")
    reason = forms.CharField(label="سبب الإعداد", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch_id"].queryset = visible_branches(actor_id, "payment.read")


class RegisterChangeForm(StyledForm):
    action = forms.ChoiceField(label="الإجراء", choices=[("rename", "تغيير الاسم"), ("disable", "تعطيل الصندوق"), ("activate", "تفعيل الصندوق")])
    name = forms.CharField(label="الاسم الجديد (عند تغيير الاسم)", max_length=200, required=False)
    reason = forms.CharField(label="سبب التغيير", max_length=300)
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


@require_http_methods(["GET"])
@secured()
def registers(request):
    rows = registers_for(request.user.pk).select_related("branch", "cash_account").order_by("branch__code", "code")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(code__icontains=q) | Q(name__icontains=q) | Q(branch__name__icontains=q))
    if request.GET.get("status") in {"active", "inactive"}:
        rows = rows.filter(active=request.GET["status"] == "active")
    return page(request, "sales/registers.html", title="صناديق البيع", active_page="registers", can_new=visible_branches(request.user.pk, "payment.read").exists(), **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured()
def register_new(request):
    require_register_admin(request.user.pk)
    form = RegisterForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, initial={"operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy()
        values["branch_id"] = values["branch_id"].pk
        result = attempt(form, lambda: create_register(request.user.pk, **values))
        if result:
            return redirect("sales-register", register_id=result.register_id)
    return page(request, "sales/register_form.html", title="إضافة صندوق بيع", active_page="registers", form=form, status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured()
def register_detail(request, register_id):
    register = get_object_or_404(registers_for(request.user.pk).select_related("branch", "cash_account"), pk=register_id)
    form = RegisterChangeForm(request.POST if request.method == "POST" else None, initial={"name": register.name, "expected_version": register.version, "operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy()
        if values["action"] != "rename":
            values.pop("name")
        result = attempt(form, lambda: change_register(request.user.pk, register_id=register.pk, **values))
        if result:
            return redirect("sales-register", register_id=result.register_id)
    history = Paginator(register.operations.select_related("created_by").order_by("-created_at", "id"), 20).get_page(request.GET.get("history_page"))
    return page(request, "sales/register.html", title=register.name, active_page="registers", register=register, form=form, history=history, status=422 if form.errors else 200)
