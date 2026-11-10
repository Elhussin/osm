import uuid
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from access.authorization import allowed, visible_branches
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from .models import StockBalance
from .tracking import PLAIN_KINDS
from .reservations import reservations_for, reserve_stock, change_reservation


def attempt(form, operation):
    try:
        return operation()
    except ValidationError as exc:
        form.add_error(None, " ".join(exc.messages))
    except (IntegrityError, ObjectDoesNotExist):
        form.add_error(None, "تغير الصنف أو الحجز المحدد. حدّث الصفحة وأعد العملية؛ لم يُحفظ أثر جزئي.")
    return None


class ReserveForm(StyledForm):
    balance = forms.ModelChoiceField(label="الصنف والفرع", queryset=StockBalance.objects.none())
    quantity = forms.IntegerField(label="الكمية", min_value=1, max_value=1000000)
    reference = forms.CharField(label="مرجع الطلب (اختياري)", required=False, max_length=100)
    reason = forms.CharField(label="سبب الحجز", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, search="", **kwargs):
        super().__init__(*args, **kwargs)
        balances = StockBalance.objects.filter(branch__in=visible_branches(actor_id, "stock.reserve"), variant__active=True,
            variant__product__active=True, variant__product__kind__in=PLAIN_KINDS).select_related("branch", "variant__product").order_by("branch__name", "variant__sku")
        if search:
            balances = balances.filter(Q(variant__sku__icontains=search) | Q(variant__barcode__icontains=search) | Q(variant__product__name__icontains=search))
        self.fields["balance"].queryset = balances.filter(pk__in=balances.values("pk")[:100])
        self.fields["balance"].label_from_instance = lambda b: f"{b.branch.name} · {b.variant.product.name} · {b.variant.sku} · المتاح {b.available} {b.variant.unit_label}"


class ActionForm(StyledForm):
    quantity = forms.IntegerField(label="الكمية للصرف أو التحرير", min_value=1, max_value=1000000, required=False)
    reason = forms.CharField(label="سبب العملية", max_length=300)
    expected_version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)
    issue_id = forms.UUIDField(widget=forms.HiddenInput, required=False)
    kind = forms.ChoiceField(choices=[("issue", "صرف"), ("release", "تحرير"), ("cancel", "إلغاء المتبقي"), ("reverse_issue", "عكس صرف")], widget=forms.HiddenInput)


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def reservations(request):
    branches = visible_branches(request.user.pk, "stock.read")
    if not branches.exists():
        raise PermissionDenied
    search = request.GET.get("q", "")[:100].strip()
    form = ReserveForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, search=search, initial={"operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        values = dict(form.cleaned_data)
        balance = values.pop("balance")
        event = attempt(form, lambda: reserve_stock(request.user.pk, branch_id=balance.branch_id, variant_id=balance.variant_id, **values))
        if event:
            return redirect("stock-reservation", reservation_id=event.reservation_id)
    rows = reservations_for(request.user.pk).select_related("branch").order_by("-created_at", "id")
    return page(request, "inventory/reservations.html", title="حجوزات المخزون", active_page="inventory", form=form,
        can_reserve=visible_branches(request.user.pk, "stock.reserve").exists(), **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def reservation_detail(request, reservation_id):
    reservation = get_object_or_404(reservations_for(request.user.pk).select_related("branch"), pk=reservation_id)
    form = ActionForm(request.POST if request.method == "POST" else None, initial={"operation_key": uuid.uuid4(), "expected_version": reservation.version})
    if request.method == "POST" and form.is_valid():
        event = attempt(form, lambda: change_reservation(request.user.pk, reservation_id=reservation.pk, **form.cleaned_data))
        if event:
            return redirect("stock-reservation", reservation_id=reservation.pk)
    events = list(reservation.events.select_related("reversal").order_by("version"))
    return page(request, "inventory/reservation.html", title="تفاصيل الحجز", active_page="inventory", reservation=reservation, events=events, form=form,
        can_reserve=allowed(request.user.pk, "stock.reserve", [reservation.branch_id]), can_issue=allowed(request.user.pk, "stock.issue", [reservation.branch_id]),
        can_reverse=allowed(request.user.pk, "stock.reverse", [reservation.branch_id]))
