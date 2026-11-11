import uuid
from django import forms
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db.models import F, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from access.authorization import allowed, require
from clinical.models import PrescriptionRevision
from inventory.models import StockPosition
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from finance.setup_views import attempt
from .models import CashShift
from .taxes import quotes_for
from .orders import orders_for, save_order, act_on_order


@require_http_methods(["GET"])
@secured()
def order_requote(request, order_id):
    order = get_object_or_404(orders_for(request.user.pk), pk=order_id, state="draft")
    require(request.user.pk, "invoice.create", [order.branch_id])
    return redirect("/sales/quotes/new/?order=" + str(order.pk) + "&order_version=" + str(order.version))


class OrderForm(StyledForm):
    shift_id = forms.ModelChoiceField(label="وردية الصندوق بعهدتك", queryset=CashShift.objects.none())
    prescription_revision_id = forms.ModelChoiceField(label="إصدار الفحص (اختياري عدا عدسات التصنيع)", queryset=PrescriptionRevision.objects.none(), required=False)
    reason = forms.CharField(label="سبب الحفظ", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)
    expected_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, quote, order=None, filters=None, **kwargs):
        super().__init__(*args, **kwargs)
        shifts = CashShift.objects.filter(branch_id=quote.branch_id, state="open", custodian_id=actor_id, pending_to__isnull=True).select_related("register")
        if order:
            shifts = shifts.filter(pk=order.shift_id)
        self.fields["shift_id"].queryset = shifts
        self.fields["shift_id"].label_from_instance = lambda item: item.register.name
        if allowed(actor_id, "prescription.read", [quote.branch_id]):
            ids = PrescriptionRevision.objects.filter(prescription__branch_id=quote.branch_id, prescription__customer_id=quote.customer_id, version=F("prescription__latest_version")).order_by("-created_at").values_list("pk", flat=True)[:50]
            self.fields["prescription_revision_id"].queryset = PrescriptionRevision.objects.filter(pk__in=ids).select_related("prescription").order_by("-created_at")
            self.fields["prescription_revision_id"].label_from_instance = lambda item: f"{item.examined_on} — إصدار {item.version}"
        self.position_fields = []
        self.tracking_searches = []
        for index, source in enumerate(quote.payload["sources"]):
            positions = StockPosition.objects.filter(branch_id=quote.branch_id, variant_id=source["catalog"]["variant_id"], on_hand__gt=F("reserved")).filter(Q(lot__isnull=True) | Q(lot__expires_on__gte=timezone.localdate())).select_related("lot").order_by("id")
            term = (filters or {}).get("tracking_" + str(index), "")[:80].strip()
            if term:
                positions = positions.filter(Q(lot__code__icontains=term) | Q(serial__icontains=term))
            # Fixed upper bound; a selected position is always rechecked by the service.
            choices = list(positions[:100])
            name = "position_" + str(index)
            field = forms.ChoiceField(label="تتبع " + source["catalog"]["sku"], required=False,
                choices=[("", "دون تتبع للصنف العادي")] + [(str(p.pk), (f"دفعة {p.lot.code} — {p.lot.expires_on}" if p.lot_id else f"تسلسل {p.serial}")) for p in choices])
            field.widget.attrs["class"] = "control"
            if source["catalog"]["specifications"].get("kind") not in {"contact_lens", "device"}:
                field.widget = forms.HiddenInput()
            else:
                self.tracking_searches.append(dict(name="tracking_"+str(index), sku=source["catalog"]["sku"], value=term))
                field.help_text = "تعرض حتى100 نتيجة متاحة؛ ضيق البحث برقم الدفعة أو التسلسل عند الحاجة."
            self.fields[name] = field
            self.position_fields.append(name)


class ActionForm(StyledForm):
    action = forms.ChoiceField(label="الإجراء", choices=[("confirm", "تأكيد وحجز الكمية"), ("cancel", "إلغاء وتحرير الحجز")])
    reason = forms.CharField(label="سبب الإجراء", max_length=300)
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


@require_http_methods(["GET"])
@secured()
def order_list(request):
    rows = orders_for(request.user.pk).select_related("branch", "customer", "current_revision__quote").order_by("-created_at", "id")
    if request.GET.get("state") in {"draft", "confirmed", "cancelled"}:
        rows = rows.filter(state=request.GET["state"])
    return page(request, "sales/orders.html", title="طلبات البيع", active_page="orders", **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured()
def order_save(request, quote_id, order_id=None):
    quote = get_object_or_404(quotes_for(request.user.pk).select_related("customer", "branch"), pk=quote_id)
    require(request.user.pk, "invoice.create", [quote.branch_id])
    if quote.customer_id is None:
        raise PermissionDenied
    order = get_object_or_404(orders_for(request.user.pk), pk=order_id) if order_id else None
    if order and request.GET.get("version") != str(order.version):
        return HttpResponse("تغير الطلب؛ أعد فتحه وراجع آخر إصدار.", status=409)
    initial = dict(operation_key=uuid.uuid4(), expected_version=order.version if order else 0)
    if order:
        initial["shift_id"] = order.shift_id
    form = OrderForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, quote=quote, order=order, initial=initial, filters=request.GET)
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy()
        positions = [values.pop(key) or None for key in form.position_fields]
        values["shift_id"] = values["shift_id"].pk
        values["prescription_revision_id"] = values["prescription_revision_id"].pk if values["prescription_revision_id"] else None
        result = attempt(form, lambda: save_order(request.user.pk, quote_id=quote.pk, order_id=order.pk if order else None, positions=positions, **values))
        if result:
            return redirect("sales-order", order_id=result.order_id)
    return page(request, "sales/order_form.html", title="مراجعة طلب البيع", active_page="orders", form=form, quote=quote, order=order, lines=zip(quote.payload["rows"], quote.payload["sources"]), status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured()
def order_detail(request, order_id):
    order = get_object_or_404(orders_for(request.user.pk).select_related("branch", "current_revision__quote"), pk=order_id)
    can_act = allowed(request.user.pk, "invoice.confirm", [order.branch_id])
    form = ActionForm(request.POST if request.method == "POST" else None, initial=dict(expected_version=order.version, operation_key=uuid.uuid4()))
    if request.method == "GET" and order.state == "confirmed":
        form.fields["action"].choices = [("cancel", "إلغاء وتحرير الحجز")]
    if request.method == "POST":
        require(request.user.pk, "invoice.confirm", [order.branch_id])
        if form.is_valid():
            result = attempt(form, lambda: act_on_order(request.user.pk, order_id=order.pk, **form.cleaned_data))
            if result:
                return redirect("sales-order", order_id=order.pk)
    events = order.events.select_related("created_by").order_by("-version")
    quote = order.current_revision.quote
    return page(request, "sales/order.html", title="طلب بيع", active_page="orders", order=order, form=form, can_act=can_act, lines=zip(quote.payload["rows"], quote.payload["sources"]), history=listing(request, events)["page_obj"], status=422 if form.errors else 200)


@require_http_methods(["GET"])
@secured()
def order_revision(request, order_id, version):
    order = get_object_or_404(orders_for(request.user.pk), pk=order_id)
    revision = get_object_or_404(order.revisions.select_related("quote"), version=version)
    return page(request, "sales/order_revision.html", title="إصدار طلب بيع", active_page="orders", order=order, revision=revision,
        lines=zip(revision.quote.payload["rows"], revision.quote.payload["sources"]))
