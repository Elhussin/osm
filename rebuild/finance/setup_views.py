import uuid
import unicodedata
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from access.authorization import allowed, require
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from .models import Account, AccountingPeriod
from .setup_services import create_account, change_account, create_period, change_period


class RequestForm(StyledForm):
    field_order = ["code", "name", "kind", "normal_side", "structure", "parent_id", "starts_on", "ends_on", "action", "reason", "expected_version", "operation_key"]
    reason = forms.CharField(label="السبب", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


class AccountForm(RequestForm):
    code = forms.CharField(label="رمز الحساب", max_length=30)
    name = forms.CharField(label="اسم الحساب", max_length=200)
    kind = forms.ChoiceField(label="تصنيف الحساب", choices=[("", "اختر التصنيف")] + Account.KINDS)
    normal_side = forms.ChoiceField(label="طبيعة الرصيد", choices=[("", "اختر الطبيعة")] + Account.SIDES)
    structure = forms.ChoiceField(label="نوع الحساب", choices=[("", "اختر النوع"), ("group", "مجموعة حسابات"), ("posting", "حساب ترحيل")])
    parent_id = forms.CharField(label="رمز المجموعة الأب (اختياري)", max_length=30, required=False, help_text="اكتب رمز مجموعة نشطة من دليل الحسابات، أو اتركه فارغًا لحساب رئيسي.")

    def clean_parent_id(self):
        code = unicodedata.normalize("NFKC", self.cleaned_data["parent_id"]).strip().upper()
        if not code:
            return None
        parent = Account.objects.filter(code=code, active=True, is_group=True, depth__lt=8).first()
        if parent is None:
            raise ValidationError("رمز الأب لا يطابق مجموعة نشطة متاحة ضمن العمق المسموح.")
        return parent


class PeriodForm(RequestForm):
    code = forms.CharField(label="رمز الفترة", max_length=30)
    name = forms.CharField(label="اسم الفترة", max_length=200)
    starts_on = forms.DateField(label="بداية الفترة", widget=forms.DateInput(attrs={"type": "date"}))
    ends_on = forms.DateField(label="نهاية الفترة", widget=forms.DateInput(attrs={"type": "date"}))


class AccountChangeForm(RequestForm):
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    action = forms.ChoiceField(label="الإجراء", choices=[("rename", "تغيير الاسم"), ("disable", "تعطيل الحساب"), ("activate", "تفعيل الحساب")])
    name = forms.CharField(label="الاسم الجديد (عند تغيير الاسم)", max_length=200, required=False)


class PeriodChangeForm(RequestForm):
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    action = forms.ChoiceField(widget=forms.HiddenInput, choices=[("close", "إغلاق"), ("reopen", "إعادة فتح")])


def attempt(form, action):
    try:
        return action()
    except ValidationError as exc:
        form.add_error(None, " ".join(exc.messages) if not hasattr(exc, "error_dict") else "راجع صحة الحقول وعدم تكرار الرمز.")
        return None


@require_http_methods(["GET"])
@secured("ledger.read")
def accounts(request):
    rows = Account.objects.select_related("parent").order_by("path")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(code__icontains=q) | Q(name__icontains=q) | Q(path__icontains=q))
    kind = request.GET.get("kind", "")
    if kind in dict(Account.KINDS):
        rows = rows.filter(kind=kind)
    state = request.GET.get("status", "")
    if state in {"active", "inactive"}:
        rows = rows.filter(active=state == "active")
    return page(request, "finance/accounts.html", title="دليل الحسابات", active_page="ledger", **listing(request, rows), kinds=Account.KINDS, selected_kind=kind, can_edit=allowed(request.user.pk, "ledger.post"))


@require_http_methods(["GET", "POST"])
@secured("ledger.read")
def account_new(request):
    require(request.user.pk, "ledger.post")
    form = AccountForm(request.POST if request.method == "POST" else None, initial={"operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        values = dict(form.cleaned_data)
        values["is_group"] = values.pop("structure") == "group"
        parent = values.pop("parent_id")
        operation = attempt(form, lambda: create_account(request.user.pk, parent_id=parent.pk if parent else None, **values))
        if operation:
            return redirect("finance-account", account_id=operation.account_id)
    return page(request, "finance/setup_form.html", title="إضافة حساب", active_page="ledger", form=form, kind="account", status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured("ledger.read")
def account_detail(request, account_id):
    account = get_object_or_404(Account.objects.select_related("parent"), pk=account_id)
    can_edit = allowed(request.user.pk, "ledger.post")
    form = AccountChangeForm(request.POST if request.method == "POST" else None, initial={"expected_version": account.version, "operation_key": uuid.uuid4(), "name": account.name})
    if request.method == "POST":
        require(request.user.pk, "ledger.post")
        if form.is_valid():
            values = dict(form.cleaned_data)
            if values["action"] != "rename":
                values.pop("name")
            operation = attempt(form, lambda: change_account(request.user.pk, account_id=account.pk, **values))
            if operation:
                messages.success(request, "حُفظ تغيير الحساب وتاريخه.")
                return redirect("finance-account", account_id=account.pk)
    return page(request, "finance/account.html", title=account.name, active_page="ledger", account=account, form=form, can_edit=can_edit, status=422 if form.errors else 200, **listing(request, account.operations.order_by("-created_at", "id")))


@require_http_methods(["GET"])
@secured("ledger.read")
def periods(request):
    rows = AccountingPeriod.objects.order_by("-starts_on", "code")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(code__icontains=q) | Q(name__icontains=q))
    if request.GET.get("status") in {"open", "closed"}:
        rows = rows.filter(state=request.GET["status"])
    return page(request, "finance/periods.html", title="الفترات المالية", active_page="ledger", can_edit=allowed(request.user.pk, "ledger.post"), **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured("ledger.read")
def period_new(request):
    require(request.user.pk, "ledger.post")
    form = PeriodForm(request.POST if request.method == "POST" else None, initial={"operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        operation = attempt(form, lambda: create_period(request.user.pk, **form.cleaned_data))
        if operation:
            return redirect("finance-period", period_id=operation.period_id)
    return page(request, "finance/setup_form.html", title="إضافة فترة مالية", active_page="ledger", form=form, kind="period", status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured("ledger.read")
def period_detail(request, period_id):
    period = get_object_or_404(AccountingPeriod, pk=period_id)
    can_edit = allowed(request.user.pk, "ledger.post")
    form = PeriodChangeForm(request.POST if request.method == "POST" else None, initial={"expected_version": period.version, "operation_key": uuid.uuid4(), "action": "close" if period.state == "open" else "reopen"})
    if request.method == "POST":
        require(request.user.pk, "ledger.post")
        if form.is_valid():
            operation = attempt(form, lambda: change_period(request.user.pk, period_id=period.pk, **form.cleaned_data))
            if operation:
                messages.success(request, "حُفظت حالة الفترة وتاريخها.")
                return redirect("finance-period", period_id=period.pk)
    return page(request, "finance/period.html", title=period.name, active_page="ledger", period=period, form=form, can_edit=can_edit, status=422 if form.errors else 200, **listing(request, period.operations.order_by("-created_at", "id")))
