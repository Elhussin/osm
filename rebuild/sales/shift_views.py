import uuid
from django import forms
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from access.authorization import allowed, visible_branches
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from finance.setup_views import attempt
from .models import CashShift, CashRegister
from .shifts import shifts_for, usable_registers, open_shift, act_on_shift, can_supervise, expected_cash


ACTIONS = [("request_handover", "طلب تسليم العهدة"), ("accept_handover", "قبول استلام العهدة"), ("cancel_handover", "إلغاء طلب التسليم"),
           ("reject_handover", "رفض استلام العهدة"), ("submit_count", "تسجيل جرد الإغلاق"), ("approve_variance", "اعتماد فرق الجرد وإغلاق الوردية")]


class RegisterChoice(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.branch.name} — {obj.code} — {obj.name}"


class ShiftOpenForm(StyledForm):
    register_id = RegisterChoice(label="الصندوق المتاح", queryset=None)
    opening_cash = forms.DecimalField(label="العهدة الافتتاحية", max_digits=18, decimal_places=2, min_value=0)
    reason = forms.CharField(label="سبب فتح الوردية", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, **kwargs):
        super().__init__(*args, **kwargs)
        registers = CashRegister.objects.filter(branch__in=visible_branches(actor_id, "payment.read")).filter(branch__in=visible_branches(actor_id, "payment.record"))
        if not self.is_bound:
            registers = registers.filter(active=True).exclude(shifts__state__in=["open", "review"])
        self.fields["register_id"].queryset = registers.select_related("branch").order_by("branch__code", "code")


class ShiftActionForm(StyledForm):
    action = forms.ChoiceField(label="إجراء الوردية", choices=ACTIONS)
    recipient_username = forms.CharField(label="اسم دخول المستلم", max_length=150, required=False, help_text="لطلب التسليم فقط؛ يقبل المستلم العهدة من حسابه بعد مراجعة الجرد.")
    counted_cash = forms.DecimalField(label="المبلغ المعدود", max_digits=18, decimal_places=2, min_value=0, required=False)
    reason = forms.CharField(label="سبب العملية", max_length=300)
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actions, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["action"].choices = [(key, label) for key, label in ACTIONS if key in actions]
            if "request_handover" not in actions:
                del self.fields["recipient_username"]
            if not set(actions) & {"request_handover", "accept_handover", "submit_count"}:
                del self.fields["counted_cash"]

    def clean(self):
        values = super().clean()
        action = values.get("action")
        if action in {"request_handover", "accept_handover", "submit_count"} and values.get("counted_cash") is None:
            self.add_error("counted_cash", "أدخل المبلغ المعدود لهذا الإجراء.")
        if action == "request_handover" and not values.get("recipient_username"):
            self.add_error("recipient_username", "أدخل اسم دخول المستلم.")
        return values


def _reader(actor_id):
    if not visible_branches(actor_id, "payment.read").exists():
        raise PermissionDenied


def shift_actions(actor_id, shift):
    if not all(allowed(actor_id, code, [shift.branch_id]) for code in ("payment.read", "payment.record")):
        return []
    supervisor = can_supervise(actor_id, shift.branch_id)
    holder = str(actor_id) == str(shift.custodian_id)
    if shift.state == "review":
        return ["approve_variance"] if supervisor else []
    if shift.state != "open":
        return []
    if shift.pending_to_id:
        result = ["cancel_handover"] if holder or supervisor else []
        if str(actor_id) == str(shift.pending_to_id):
            result += ["accept_handover", "reject_handover"]
        return result
    return ["request_handover", "submit_count"] if holder else (["submit_count"] if supervisor else [])


@require_http_methods(["GET"])
@secured()
def shift_list(request):
    _reader(request.user.pk)
    rows = shifts_for(request.user.pk).select_related("branch", "custodian", "pending_to").order_by("-opened_at", "id")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(register_snapshot__code__icontains=q) | Q(register_snapshot__name__icontains=q) | Q(custodian__username__icontains=q))
    if request.GET.get("status") in dict(CashShift.STATES):
        rows = rows.filter(state=request.GET["status"])
    return page(request, "sales/shifts.html", title="الورديات والعهدة", active_page="shifts", states=CashShift.STATES,
        can_open=usable_registers(request.user.pk).exclude(shifts__state__in=["open", "review"]).exists(), **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured()
def shift_new(request):
    _reader(request.user.pk)
    if request.method == "GET" and not usable_registers(request.user.pk).exists():
        raise PermissionDenied
    form = ShiftOpenForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk,
        initial={"operation_key": uuid.uuid4(), "register_id": request.GET.get("register")})
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy()
        values["register_id"] = values["register_id"].pk
        result = attempt(form, lambda: open_shift(request.user.pk, **values))
        if result:
            return redirect("sales-shift", shift_id=result.shift_id)
    return page(request, "sales/shift_form.html", title="فتح وردية", active_page="shifts", form=form, status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured()
def shift_detail(request, shift_id):
    _reader(request.user.pk)
    shift = get_object_or_404(shifts_for(request.user.pk).select_related("branch", "custodian", "pending_to"), pk=shift_id)
    actions = shift_actions(request.user.pk, shift)
    form = ShiftActionForm(request.POST if request.method == "POST" else None, actions=actions,
        initial={"expected_version": shift.version, "operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        values = {key: form.cleaned_data[key] for key in ("action", "reason", "expected_version", "operation_key")}
        if values["action"] in {"request_handover", "accept_handover", "submit_count"}:
            values["counted_cash"] = form.cleaned_data["counted_cash"]
        if values["action"] == "request_handover":
            values["recipient_username"] = form.cleaned_data["recipient_username"]
        result = attempt(form, lambda: act_on_shift(request.user.pk, shift_id=shift.pk, **values))
        if result:
            return redirect("sales-shift", shift_id=result.shift_id)
    history = Paginator(shift.events.select_related("created_by").order_by("-version"), 20).get_page(request.GET.get("history_page"))
    return page(request, "sales/shift.html", title="وردية " + shift.display_code, active_page="shifts", shift=shift, actions=actions,
        current_expected=expected_cash(shift), form=form, history=history, status=422 if form.errors else 200)
