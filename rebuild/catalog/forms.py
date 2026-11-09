from decimal import Decimal
from uuid import UUID
from django import forms
from django.core.exceptions import ValidationError
from access.authorization import visible_branches, allowed
from clinical.models import Customer
from workspace.forms import StyledForm
from .models import KINDS, UNITS, CHANNELS
from .specifications import SCHEMAS, canonical_specs


class ProductForm(StyledForm):
    code_value = forms.CharField(label="رمز المنتج", max_length=40)
    name = forms.CharField(label="اسم المنتج", max_length=200)
    kind = forms.ChoiceField(label="نوع المنتج", choices=KINDS)
    brand = forms.CharField(label="العلامة التجارية", max_length=100, required=False)
    model = forms.CharField(label="الموديل", max_length=100, required=False)


class ProductEditForm(StyledForm):
    name = forms.CharField(label="اسم المنتج", max_length=200)
    brand = forms.CharField(label="العلامة التجارية", max_length=100, required=False)
    model = forms.CharField(label="الموديل", max_length=100, required=False)
    active = forms.ChoiceField(label="الحالة", choices=[("true", "نشط"), ("false", "موقوف")])
    expected_version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)

    def clean_active(self):
        return self.cleaned_data["active"] == "true"


class VariantForm(StyledForm):
    sku = forms.CharField(label="رمز المتغير SKU", max_length=60)
    barcode = forms.CharField(label="الباركود (اختياري)", max_length=80, required=False)
    unit = forms.ChoiceField(label="وحدة البيع", choices=UNITS)
    base_price = forms.DecimalField(label="السعر الأساسي للوحدة — ريال، قبل الضريبة", min_value=0, max_digits=12, decimal_places=2)

    def __init__(self, *args, kind, **kwargs):
        super().__init__(*args, **kwargs)
        self.kind = kind
        units = {"piece", "pair"} if kind in {"stock_lens", "rx_lens"} else ({"box"} if kind == "contact_lens" else ({"service"} if kind == "service" else {"piece"}))
        self.fields["unit"].choices = [(key, label) for key, label in UNITS if key in units]
        for key, spec in SCHEMAS[kind].items():
            options = {"label": spec.label, "required": spec.required}
            if spec.type in {"integer", "decimal"}:
                options.update(min_value=Decimal(spec.minimum), max_value=Decimal(spec.maximum))
                field = forms.IntegerField(**options) if spec.type == "integer" else forms.DecimalField(**options, max_digits=6, decimal_places=2)
                field.widget.attrs["step"] = "1" if spec.type == "integer" else spec.step
            elif spec.type == "choice":
                field = forms.ChoiceField(**options, choices=spec.choices)
            else:
                field = forms.CharField(**options, max_length=1200 if spec.type == "tokens" else 100)
            field.widget.attrs.update({"class": "control", "aria-label": spec.label})
            self.fields["spec_" + key] = field

    def specifications(self):
        return {key: self.cleaned_data.get("spec_" + key) for key in SCHEMAS[self.kind]}

    def clean(self):
        data = super().clean()
        if not self.errors:
            try:
                canonical_specs(self.kind, self.specifications(), data["unit"])
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for key, errors in exc.message_dict.items():
                        self.add_error("spec_" + key if "spec_" + key in self.fields else (key if key in self.fields else None), errors)
                else:
                    self.add_error(None, exc)
        return data


class VariantEditForm(StyledForm):
    base_price = forms.DecimalField(label="السعر الأساسي للوحدة — ريال، قبل الضريبة", min_value=0, max_digits=12, decimal_places=2)
    active = forms.ChoiceField(label="الحالة", choices=[("true", "نشط"), ("false", "موقوف")])
    expected_version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)

    def clean_active(self):
        return self.cleaned_data["active"] == "true"


class ScopeForm(StyledForm):
    branch_id = forms.ModelChoiceField(label="الفرع", queryset=None, required=False, empty_label="كل الفروع")
    customer_id = forms.ModelChoiceField(label="العميل (اختياري)", queryset=None, required=False, empty_label="كل العملاء", help_text="اختر الفرع ثم اضغط تحديث خيارات العملاء، إن أردت سعر عميل محدد.")
    channel = forms.ChoiceField(label="قناة السعر", choices=CHANNELS)

    def __init__(self, *args, actor_id, branch_id=None, quoting=False, **kwargs):
        super().__init__(*args, **kwargs)
        branches = visible_branches(actor_id, "invoice.read" if quoting else "catalog.manage")
        self.fields["branch_id"].queryset = branches
        self.fields["branch_id"].label_from_instance = lambda b: f"{b.name} · {b.code}"
        self.fields["branch_id"].required = quoting
        if quoting:
            self.fields["branch_id"].empty_label = "اختر الفرع"
        self.fields["customer_id"].queryset = Customer.objects.none()
        try:
            parsed = UUID(str(branch_id))
        except (ValueError, TypeError, AttributeError):
            parsed = None
        if parsed and branches.filter(pk=parsed).exists() and allowed(actor_id, "customer.read", [parsed]):
            self.fields["customer_id"].queryset = Customer.objects.filter(branch_links__branch_id=parsed, active=True).order_by("first_name", "id")
        self.fields["customer_id"].label_from_instance = lambda customer: customer.full_name

    def clean(self):
        data = super().clean()
        if data.get("customer_id") and not data.get("branch_id"):
            self.add_error("branch_id", "حدد فرع العميل.")
        return data


class RuleForm(ScopeForm):
    min_quantity = forms.IntegerField(label="يبدأ من كمية", min_value=1, max_value=1000000, initial=1)
    unit_price = forms.DecimalField(label="سعر الوحدة — ريال، قبل الضريبة", min_value=0, max_digits=12, decimal_places=2)
    valid_from = forms.DateField(label="من تاريخ", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    valid_until = forms.DateField(label="حتى تاريخ (شامل، اختياري)", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))


class QuoteForm(ScopeForm):
    count = forms.IntegerField(label="الكمية بوحدة البيع", min_value=1, max_value=1000000, initial=1)
    as_of = forms.DateField(label="تاريخ التسعير", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
