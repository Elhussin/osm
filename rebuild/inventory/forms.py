from django import forms
from access.authorization import visible_branches
from catalog.models import Variant
from workspace.forms import StyledForm
from .matrix import axes


def family_label(variant):
    values = variant.specifications["values"]
    coatings = "+".join(values.get("coatings", [])) or "بدون طلاءات"
    design = {"single": "أحادية", "bifocal": "ثنائية", "progressive": "متدرجة"}.get(values.get("design"), "")
    return f"{values.get('material')} · {values.get('index')} · {values.get('diameter')}mm · {design} · {values.get('color') or 'بدون لون'} · {coatings} · {variant.unit_label}"


def families(product):
    return Variant.objects.filter(product=product, matrix_family__isnull=False).select_related("product").order_by("matrix_family", "-active", "sku").distinct("matrix_family")


class MatrixFilterForm(StyledForm):
    branch_id = forms.ModelChoiceField(label="الفرع / المستودع", queryset=None)
    template_id = forms.ModelChoiceField(label="عائلة الصنف ووحدة البيع", queryset=None)
    sphere_min = forms.DecimalField(label="SPH من", min_value=-40, max_value=40, decimal_places=2, initial="-2")
    sphere_max = forms.DecimalField(label="SPH إلى", min_value=-40, max_value=40, decimal_places=2, initial="2")
    cylinder_min = forms.DecimalField(label="CYL من", min_value=-20, max_value=20, decimal_places=2, initial="-2")
    cylinder_max = forms.DecimalField(label="CYL إلى", min_value=-20, max_value=20, decimal_places=2, initial="0")

    def __init__(self, *args, actor_id, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch_id"].queryset = visible_branches(actor_id, "stock.read")
        self.fields["branch_id"].label_from_instance = lambda branch: f"{branch.name} · {branch.code}"
        self.fields["template_id"].queryset = families(product)
        self.fields["template_id"].label_from_instance = family_label
        for key in ("sphere_min", "sphere_max", "cylinder_min", "cylinder_max"):
            self.fields[key].widget.attrs.update({"step": "0.25", "dir": "ltr"})

    def clean(self):
        values = super().clean()
        if not self.errors:
            self.matrix_axes = axes(**{key: values[key] for key in ("sphere_min", "sphere_max", "cylinder_min", "cylinder_max")})
        return values


class MatrixEntryForm(StyledForm):
    operation_key = forms.UUIDField(widget=forms.HiddenInput)
    template_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    reference = forms.CharField(label="مرجع الإضافة (اختياري)", max_length=100, required=False)
    reason = forms.CharField(label="سبب الإضافة", max_length=300)
    create_missing = forms.ChoiceField(label="المتغيرات الناقصة", choices=[("no", "إضافة للموجود فقط"), ("yes", "إنشاء الناقص بمواصفات وسعر القالب")], initial="no")

    def clean_create_missing(self):
        return self.cleaned_data["create_missing"] == "yes"


class ReverseForm(StyledForm):
    operation_key = forms.UUIDField(widget=forms.HiddenInput)
    reason = forms.CharField(label="سبب العكس", max_length=300)


class ConfirmForm(StyledForm):
    preview_token = forms.CharField(widget=forms.HiddenInput, max_length=150000)
