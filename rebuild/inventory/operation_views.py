import uuid
from django import forms
from django.core.exceptions import PermissionDenied
from django.core.validators import MinValueValidator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from access.models import Branch
from access.authorization import allowed, visible_branches, authorization_state
from access.policy import permits, ResourceScope
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from .models import StockBalance
from .operations import post_operation, reverse_operation, operations_for
from .reservation_views import attempt


class OperationForm(StyledForm):
    quantity = forms.IntegerField(label="الكمية", min_value=0, max_value=1000000)
    destination_id = forms.ModelChoiceField(label="الفرع الوجهة", queryset=Branch.objects.none(), required=False)
    reference = forms.CharField(label="المرجع (اختياري)", max_length=100, required=False)
    reason = forms.CharField(label="سبب العملية", max_length=300)
    expected_version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, balance, kind, **kwargs):
        super().__init__(*args, **kwargs)
        if kind == "transfer":
            self.fields["quantity"].min_value = 1
            self.fields["quantity"].validators.append(MinValueValidator(1))
            self.fields["quantity"].widget.attrs["min"] = 1
            self.fields["quantity"].label = "الكمية المحولة"
            self.fields["destination_id"].required = True
            self.fields["destination_id"].queryset = visible_branches(actor_id, "stock.transfer").exclude(pk=balance.branch_id)
        else:
            self.fields["quantity"].label = "الكمية الفعلية المعدودة"
            del self.fields["destination_id"]
        self.fields["quantity"].widget.attrs["aria-label"] = self.fields["quantity"].label


class ReversalForm(StyledForm):
    reason = forms.CharField(label="سبب العكس", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


def balances_for(actor_id):
    return StockBalance.objects.filter(branch__in=visible_branches(actor_id, "stock.read"), variant__product__kind="stock_lens").select_related("branch", "variant__product")


@require_http_methods(["GET"])
@secured("catalog.read")
def operation_list(request):
    if not visible_branches(request.user.pk, "stock.read").exists():
        raise PermissionDenied
    rows = balances_for(request.user.pk).order_by("branch__name", "variant__sku")
    search = request.GET.get("q", "")[:100].strip()
    if search:
        rows = rows.filter(Q(variant__sku__icontains=search) | Q(variant__barcode__icontains=search) | Q(variant__product__name__icontains=search))
    result = listing(request, rows)
    state = authorization_state(request.user.pk)
    if state is None:
        raise PermissionDenied
    principal, context, grants = state
    for balance in result["page_obj"]:
        resource = ResourceScope(context.company_id, frozenset([str(balance.branch_id)]))
        balance.can_transfer = permits(principal, context, "stock.transfer", resource, grants)
        balance.can_count = permits(principal, context, "stock.count", resource, grants)
    documents = operations_for(request.user.pk).select_related("source", "destination").order_by("-created_at", "id")[:20]
    return page(request, "inventory/operations.html", title="التحويل والجرد", active_page="inventory", documents=documents, **result)


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def operation_new(request, balance_id, kind):
    if kind not in {"transfer", "count"}:
        from django.http import Http404
        raise Http404
    balance = get_object_or_404(balances_for(request.user.pk), pk=balance_id)
    if not allowed(request.user.pk, "stock.transfer" if kind == "transfer" else "stock.count", [balance.branch_id]):
        raise PermissionDenied
    form = OperationForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, balance=balance, kind=kind,
        initial={"expected_version": balance.version, "operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        values = dict(form.cleaned_data)
        destination = values.pop("destination_id", None)
        document = attempt(form, lambda: post_operation(request.user.pk, source_balance_id=balance.pk, kind=kind,
            destination_id=destination.pk if destination else None, **values))
        if document:
            return redirect("stock-operation", operation_id=document.pk)
    return page(request, "inventory/operation_form.html", title="تحويل مخزون" if kind == "transfer" else "جرد مخزون",
        active_page="inventory", balance=balance, kind=kind, form=form)


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def operation_detail(request, operation_id):
    document = get_object_or_404(operations_for(request.user.pk).select_related("source", "destination", "reversal", "reverses"), pk=operation_id)
    branches = [document.source_id] + ([document.destination_id] if document.destination_id else [])
    can_reverse = document.kind != "reversal" and not hasattr(document, "reversal") and allowed(request.user.pk, "stock.reverse", branches)
    form = ReversalForm(request.POST if request.method == "POST" else None, initial={"operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        reversal = attempt(form, lambda: reverse_operation(request.user.pk, operation_id=document.pk, **form.cleaned_data))
        if reversal:
            return redirect("stock-operation", operation_id=reversal.pk)
    return page(request, "inventory/operation.html", title=document.get_kind_display(), active_page="inventory", document=document,
        movements=document.movements.select_related("branch").order_by("branch__name"), can_reverse=can_reverse, form=form)
