import uuid
from django import forms
from django.core.exceptions import PermissionDenied
from django.core.validators import MaxValueValidator
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from access.authorization import visible_branches, allowed, authorization_state
from access.policy import permits, ResourceScope
from catalog.models import Variant
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from .models import StockBalance, StockPosition, StockMovement
from .tracking import STOCK_KINDS
from .receiving import receive_stock
from .reservations import reserve_stock
from .operations import post_operation
from .operation_views import OperationForm
from .reservation_views import attempt


def read_branches(actor_id):
    branches = visible_branches(actor_id, "stock.read")
    if not branches.exists():
        raise PermissionDenied
    return branches


class ReceiveForm(StyledForm):
    branch_id = forms.ModelChoiceField(label="الفرع / المستودع", queryset=StockBalance.objects.none())
    quantity = forms.IntegerField(label="الكمية المستلمة بوحدة الصنف", min_value=1, max_value=1000000)
    lot_code = forms.CharField(label="رقم الدفعة", max_length=80)
    expires_on = forms.DateField(label="تاريخ الصلاحية", widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}))
    serial = forms.CharField(label="الرقم التسلسلي للوحدة", max_length=80)
    reference = forms.CharField(label="المرجع (اختياري)", max_length=100, required=False)
    reason = forms.CharField(label="سبب الإضافة", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, variant, **kwargs):
        super().__init__(*args, **kwargs)
        readable = visible_branches(actor_id, "stock.read")
        self.fields["branch_id"].queryset = visible_branches(actor_id, "stock.receive").filter(pk__in=readable)
        if variant.product.kind != "contact_lens":
            del self.fields["lot_code"], self.fields["expires_on"]
        if variant.product.kind != "device":
            del self.fields["serial"]
        else:
            self.fields["quantity"].validators.append(MaxValueValidator(1))
            self.fields["quantity"].widget.attrs["max"] = 1
            self.fields["quantity"].initial = 1


class HoldForm(StyledForm):
    quantity = forms.IntegerField(label="الكمية المحجوزة", min_value=1, max_value=1000000)
    reference = forms.CharField(label="مرجع الطلب (اختياري)", max_length=100, required=False)
    reason = forms.CharField(label="سبب الحجز", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


class PositionOperationForm(OperationForm):
    expected_position_version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)

    def __init__(self, *args, position, **kwargs):
        super().__init__(*args, **kwargs)
        if position.serial:
            self.fields["quantity"].validators.append(MaxValueValidator(1))
            self.fields["quantity"].widget.attrs["max"] = 1


@require_http_methods(["GET"])
@secured("catalog.read")
def home(request):
    read_branches(request.user.pk)
    return page(request, "inventory/home.html", title="المخزون", active_page="inventory")


@require_http_methods(["GET"])
@secured("catalog.read")
def receiving_catalog(request):
    read_branches(request.user.pk)
    rows = Variant.objects.select_related("product").filter(active=True, product__active=True, product__kind__in=STOCK_KINDS).order_by("product__name", "sku")
    search = request.GET.get("q", "")[:100].strip()
    if search:
        rows = rows.filter(Q(sku__icontains=search) | Q(barcode__icontains=search) | Q(product__name__icontains=search))
    return page(request, "inventory/receiving_catalog.html", title="استلام المخزون", active_page="inventory", **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def receiving(request, variant_id):
    read_branches(request.user.pk)
    if not visible_branches(request.user.pk, "stock.receive").exists():
        raise PermissionDenied
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=variant_id, active=True, product__active=True, product__kind__in=STOCK_KINDS)
    form = ReceiveForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, variant=variant,
        initial={"operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        values = dict(form.cleaned_data)
        values["branch_id"] = values["branch_id"].pk
        document = attempt(form, lambda: receive_stock(request.user.pk, variant_id=variant.pk, **values))
        if document:
            return redirect("stock-receipt", receipt_id=document.pk)
    return page(request, "inventory/receiving.html", title="استلام مخزون", active_page="inventory", variant=variant, form=form)


def positions_for(actor_id):
    return StockPosition.objects.filter(branch__in=visible_branches(actor_id, "stock.read")).select_related("variant__product", "lot", "branch")


@require_http_methods(["GET"])
@secured("catalog.read")
def positions(request):
    read_branches(request.user.pk)
    rows = positions_for(request.user.pk).order_by("lot__expires_on", "variant__sku", "id")
    search = request.GET.get("q", "")[:100].strip()
    if search:
        rows = rows.filter(Q(variant__sku__icontains=search) | Q(variant__barcode__icontains=search) | Q(variant__product__name__icontains=search) | Q(lot__code__icontains=search) | Q(serial__icontains=search))
    result = listing(request, rows)
    state = authorization_state(request.user.pk)
    if state is None:
        raise PermissionDenied
    principal, context, grants = state
    today = timezone.localdate()
    for position in result["page_obj"]:
        resource = ResourceScope(context.company_id, frozenset([str(position.branch_id)]))
        position.expired = bool(position.lot_id and position.lot.expires_on < today)
        position.usable_quantity = 0 if position.expired or not position.variant.active or not position.variant.product.active else position.available
        position.can_reserve = position.usable_quantity > 0 and permits(principal, context, "stock.reserve", resource, grants)
        position.can_transfer = permits(principal, context, "stock.transfer", resource, grants)
        position.can_count = permits(principal, context, "stock.count", resource, grants)
    return page(request, "inventory/positions.html", title="الدفعات والوحدات التسلسلية", active_page="inventory", **result)


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def position_action(request, position_id, action):
    if action not in {"reserve", "transfer", "count"}:
        from django.http import Http404
        raise Http404
    position = get_object_or_404(positions_for(request.user.pk), pk=position_id)
    permission = {"reserve": "stock.reserve", "transfer": "stock.transfer", "count": "stock.count"}[action]
    if not allowed(request.user.pk, permission, [position.branch_id]):
        raise PermissionDenied
    balance = get_object_or_404(StockBalance, branch_id=position.branch_id, variant_id=position.variant_id)
    initial = {"operation_key": uuid.uuid4(), "expected_version": balance.version, "expected_position_version": position.version}
    if action == "reserve":
        form = HoldForm(request.POST if request.method == "POST" else None, initial=initial)
    else:
        form = PositionOperationForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, balance=balance,
            position=position, kind=action, initial=initial)
    if request.method == "POST" and form.is_valid():
        values = dict(form.cleaned_data)
        if action == "reserve":
            document = attempt(form, lambda: reserve_stock(request.user.pk, branch_id=position.branch_id, variant_id=position.variant_id, position_id=position.pk, **values))
            if document:
                return redirect("stock-reservation", reservation_id=document.reservation_id)
        else:
            destination = values.pop("destination_id", None)
            document = attempt(form, lambda: post_operation(request.user.pk, source_balance_id=balance.pk, kind=action, position_id=position.pk,
                destination_id=destination.pk if destination else None, **values))
            if document:
                return redirect("stock-operation", operation_id=document.pk)
    return page(request, "inventory/position_form.html", title={"reserve": "حجز دفعة أو وحدة", "transfer": "تحويل دفعة أو وحدة", "count": "جرد دفعة أو وحدة"}[action],
        active_page="inventory", position=position, balance=balance, action=action, form=form)


@require_http_methods(["GET"])
@secured("catalog.read")
def trace(request):
    branches = read_branches(request.user.pk)
    rows = StockMovement.objects.filter(branch__in=branches).select_related("branch", "receipt", "reservation_event", "operation").annotate(
        posted_at=Coalesce("receipt__created_at", "reservation_event__created_at", "operation__created_at")).order_by("-posted_at", "id")
    search = request.GET.get("q", "")[:100].strip()
    if search:
        rows = rows.filter(Q(variant__sku__icontains=search) | Q(position__lot__code__icontains=search) | Q(position__serial__icontains=search))
    return page(request, "inventory/trace.html", title="سجل حركات المخزون", active_page="inventory", **listing(request, rows))
