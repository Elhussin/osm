from django import forms
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_GET
from access.models import Branch
from access.authorization import visible_branches
from workspace.forms import StyledForm
from workspace.views import secured, page
from .reports import trial_balance, account_ledger


class ReportForm(StyledForm):
    starts_on = forms.DateField(label="من تاريخ", widget=forms.DateInput(attrs={"type": "date"}))
    ends_on = forms.DateField(label="إلى تاريخ", widget=forms.DateInput(attrs={"type": "date"}))
    branch_id = forms.ModelChoiceField(label="الفرع", queryset=Branch.objects.none(), required=False, empty_label="كل الفروع المصرح بها")

    def __init__(self, *args, actor_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch_id"].queryset = visible_branches(actor_id, "ledger.read")

    def clean(self):
        values = super().clean()
        if values.get("starts_on") and values.get("ends_on") and values["starts_on"] > values["ends_on"]:
            raise forms.ValidationError("نهاية المدة تسبق بدايتها.")
        return values


class LedgerForm(ReportForm):
    account_code = forms.CharField(label="رمز حساب الترحيل", max_length=30)


def _form(request, form_class):
    today = timezone.localdate()
    values = request.GET.copy()
    if not request.GET:
        if form_class is LedgerForm:
            return form_class(actor_id=request.user.pk, initial={"starts_on": today.replace(day=1), "ends_on": today})
        values.update(starts_on=today.replace(day=1).isoformat(), ends_on=today.isoformat())
    return form_class(values, actor_id=request.user.pk)


def _arguments(form):
    values = form.cleaned_data.copy()
    values["branch_id"] = values["branch_id"].pk if values["branch_id"] else None
    return values


@require_GET
@secured("ledger.read")
def trial(request):
    form = _form(request, ReportForm)
    report = None
    context = {}
    if form.is_valid():
        report = trial_balance(request.user.pk, **_arguments(form))
        q = request.GET.get("q", "")[:100].strip()
        rows = [row for row in report["rows"] if not q or q.casefold() in (row["code"] + " " + row["name"]).casefold()]
        params = request.GET.copy()
        params.pop("page", None)
        params.setdefault("starts_on", report["starts_on"].isoformat())
        params.setdefault("ends_on", report["ends_on"].isoformat())
        context.update(page_obj=Paginator(rows, 20).get_page(request.GET.get("page")), query_params=params.urlencode(), q=q)
    return page(request, "finance/trial_balance.html", title="ميزان المراجعة والمطابقة", active_page="ledger", form=form, report=report, **context)


@require_GET
@secured("ledger.read")
def ledger(request):
    form = _form(request, LedgerForm)
    report = None
    if form.is_valid():
        try:
            report = account_ledger(request.user.pk, **_arguments(form), page=request.GET.get("page", 1))
        except ValidationError as exc:
            form.add_error("account_code", exc)
    params = request.GET.copy()
    params.pop("page", None)
    return page(request, "finance/account_ledger.html", title="دفتر الحساب", active_page="ledger", form=form, report=report, query_params=params.urlencode())
