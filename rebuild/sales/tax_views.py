import uuid
from django import forms
from django.forms import formset_factory
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from access.authorization import require, allowed, visible_branches
from access.models import Branch
from catalog.models import Variant
from clinical.models import Customer
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from finance.setup_views import attempt
from .models import TaxTreatmentRevision
from .tax_codes import REASONS
from .taxes import require_tax_reader, revise_treatment, quotes_for, create_tax_quote


class TreatmentForm(StyledForm):
    valid_from = forms.DateField(label="ساري من", widget=forms.DateInput(attrs={"type": "date"}))
    state = forms.ChoiceField(label="قرار المراجعة", choices=TaxTreatmentRevision.STATES)
    category = forms.ChoiceField(label="الفئة (للمراجع فقط)", required=False, choices=[("", "اختر بعد المراجعة"), ("S", "S — أساسي 15%"), ("Z", "Z — صفري"), ("E", "E — معفى"), ("O", "O — خارج النطاق")])
    reason_code = forms.ChoiceField(label="رمز سبب الاستثناء", required=False, choices=[("", "دون سبب للفئة S")] + [(code, code + " — " + value[1]) for code, value in REASONS.items()])
    exception_text = forms.CharField(label="وصف خارج النطاق O", required=False, max_length=300)
    basis = forms.CharField(label="مرجع المراجعة والتصنيف", max_length=500)
    reason = forms.CharField(label="سبب التغيير", max_length=300)
    expected_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


class QuoteForm(StyledForm):
    branch_id = forms.ModelChoiceField(label="الفرع", queryset=Branch.objects.none())
    as_of = forms.DateField(label="تاريخ المعاينة", widget=forms.DateInput(attrs={"type": "date"}))
    document_discount_kind = forms.ChoiceField(label="نوع خصم الإجمالي", choices=[("amount", "مبلغ"), ("percent", "نسبة %")])
    document_discount_value = forms.DecimalField(label="خصم الإجمالي بعد خصم البنود", min_value=0, max_digits=18, decimal_places=2, initial=0)
    customer_identifier = forms.CharField(label="معرف العميل (اختياري)", required=False, max_length=30)
    reason = forms.CharField(label="وصف المعاينة", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch_id"].queryset = visible_branches(actor_id, "invoice.read").filter(pk__in=visible_branches(actor_id, "invoice.create"))


class LineForm(StyledForm):
    sku = forms.CharField(label="رمز SKU", max_length=60)
    quantity = forms.IntegerField(label="الكمية", min_value=1, max_value=1000000, initial=1)
    price_basis = forms.ChoiceField(label="مصدر السعر", choices=[("gross", "سعر نهائي شامل الضريبة عند انطباقها"), ("catalog_net", "الكتالوج قبل الضريبة — تحويل صريح")])
    unit_amount = forms.DecimalField(label="السعر النهائي للوحدة (اتركه فارغًا للكتالوج)", required=False, min_value=0, max_digits=12, decimal_places=2)
    discount_kind = forms.ChoiceField(label="نوع خصم البند", choices=[("amount", "مبلغ"), ("percent", "نسبة %")])
    discount_value = forms.DecimalField(label="خصم البند", min_value=0, max_digits=18, decimal_places=2, initial=0)

    def clean(self):
        values = super().clean()
        if values.get("price_basis") == "gross" and values.get("unit_amount") is None:
            self.add_error("unit_amount", "أدخل السعر النهائي.")
        if values.get("price_basis") == "catalog_net" and values.get("unit_amount") is not None:
            self.add_error("unit_amount", "اترك السعر فارغًا لقراءته من الكتالوج.")
        return values


Lines = formset_factory(LineForm, extra=0, min_num=1, max_num=40, validate_min=True, validate_max=True, absolute_max=40, can_delete=True)


@require_http_methods(["GET"])
@secured()
def treatments(request):
    require_tax_reader(request.user.pk)
    rows = Variant.objects.select_related("product").order_by("sku")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(sku__icontains=q) | Q(product__name__icontains=q))
    return page(request, "sales/treatments.html", title="تصنيف الأصناف الضريبي", active_page="taxes", **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured()
def treatment_detail(request, variant_id):
    require_tax_reader(request.user.pk)
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=variant_id)
    history = variant.tax_revisions.order_by("-version")
    latest = history.first()
    can_edit = allowed(request.user.pk, "ledger.post")
    if request.method == "POST":
        require(request.user.pk, "ledger.post")
    form = TreatmentForm(request.POST if request.method == "POST" else None, initial={"valid_from": timezone.localdate(), "expected_version": latest.version if latest else 0, "operation_key": uuid.uuid4()})
    if request.method == "POST" and form.is_valid():
        result = attempt(form, lambda: revise_treatment(request.user.pk, variant_id=variant.pk, **form.cleaned_data))
        if result:
            return redirect("sales-treatment", variant_id=variant.pk)
    return page(request, "sales/treatment.html", title=variant.sku, active_page="taxes", variant=variant, history=listing(request, history)["page_obj"], form=form, can_edit=can_edit, status=422 if form.errors else 200)


@require_http_methods(["GET"])
@secured()
def quote_list(request):
    rows = quotes_for(request.user.pk).select_related("branch").order_by("-created_at", "id")
    return page(request, "sales/quotes.html", title="معاينات مبالغ البيع", active_page="quotes", **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured()
def quote_new(request):
    require(request.user.pk, "catalog.read")
    form = QuoteForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk, initial={"as_of": timezone.localdate(), "operation_key": uuid.uuid4()})
    rows = Lines(request.POST if request.method == "POST" else None, prefix="lines")
    if request.method == "POST" and request.POST.get("action") == "add":
        # Add one row without JavaScript, without persisting a quote or altering entered values.
        data = request.POST.copy()
        try:
            count = int(data.get("lines-TOTAL_FORMS", "0"))
        except ValueError:
            count = 40
        if 1 <= count < 40:
            data["lines-TOTAL_FORMS"] = str(count + 1)
            data[f"lines-{count}-quantity"] = "1"
            data[f"lines-{count}-price_basis"] = "gross"
            data[f"lines-{count}-discount_kind"] = "amount"
            data[f"lines-{count}-discount_value"] = "0"
            rows = Lines(data, prefix="lines")
        return page(request, "sales/quote_form.html", title="معاينة مبالغ البيع", active_page="quotes", form=form, rows=rows)
    if request.method == "POST" and form.is_valid() and rows.is_valid():
        values = form.cleaned_data.copy()
        identifier = values.pop("customer_identifier")
        branch = values.pop("branch_id")
        customer_id = None
        if identifier:
            require(request.user.pk, "customer.read", [branch.pk])
            customer = Customer.objects.filter(identifier=identifier, active=True, branch_links__branch=branch).first()
            if customer is None:
                form.add_error("customer_identifier", "العميل غير متاح في هذا الفرع.")
            else:
                customer_id = customer.pk
        if not form.errors:
            result = attempt(form, lambda: create_tax_quote(request.user.pk, branch_id=branch.pk, customer_id=customer_id,
                lines=[{key: value for key, value in row.items() if key != "DELETE"} for row in rows.cleaned_data if row and not row.get("DELETE")], **values))
            if result:
                return redirect("sales-quote", quote_id=result.pk)
    return page(request, "sales/quote_form.html", title="معاينة مبالغ البيع", active_page="quotes", form=form, rows=rows, status=422 if form.errors or rows.errors or rows.non_form_errors() else 200)


@require_http_methods(["GET"])
@secured()
def quote_detail(request, quote_id):
    quote = get_object_or_404(quotes_for(request.user.pk).select_related("branch"), pk=quote_id)
    lines = zip(quote.payload["rows"], quote.payload["sources"])
    return page(request, "sales/quote.html", title="معاينة محفوظة", active_page="quotes", quote=quote, lines=lines)
