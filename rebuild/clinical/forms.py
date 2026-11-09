from django import forms
from django.core.exceptions import ValidationError
from access.authorization import visible_branches
from workspace.forms import StyledForm
from .validation import customer_values, validate_measurements, MEASUREMENTS, RANGES


class CustomerForm(StyledForm):
    first_name = forms.CharField(label="الاسم الأول", max_length=100)
    last_name = forms.CharField(label="اسم العائلة", max_length=100, required=False)
    identifier = forms.CharField(label="رقم الهوية أو الوثيقة", max_length=30, required=False)
    phone = forms.CharField(label="رقم الهاتف", max_length=30, required=False)
    email = forms.EmailField(label="البريد الإلكتروني", required=False)
    date_of_birth = forms.DateField(label="تاريخ الميلاد", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    expected_version = forms.IntegerField(widget=forms.HiddenInput, required=False, min_value=1)

    def clean(self):
        data = super().clean()
        if not self.errors:
            data.update(customer_values(data))
        return data


class NewCustomerForm(CustomerForm):
    branch_id = forms.ModelChoiceField(label="الفرع", queryset=None)

    def __init__(self, *args, actor_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch_id"].queryset = visible_branches(actor_id, "customer.write")
        self.fields["branch_id"].label_from_instance = lambda b: f"{b.name} · {b.code}"


class ShareForm(StyledForm):
    source_branch_id = forms.ModelChoiceField(label="الفرع الحالي", queryset=None)
    target_branch_id = forms.ModelChoiceField(label="مشاركة مع الفرع", queryset=None)

    def __init__(self, *args, actor_id, customer, **kwargs):
        super().__init__(*args, **kwargs)
        branches = visible_branches(actor_id, "customer.write")
        self.fields["source_branch_id"].queryset = branches.filter(customerbranchaccess__customer=customer)
        self.fields["target_branch_id"].queryset = branches.exclude(customerbranchaccess__customer=customer)
        for key in ("source_branch_id", "target_branch_id"):
            self.fields[key].label_from_instance = lambda b: f"{b.name} · {b.code}"


class PrescriptionForm(StyledForm):
    examined_on = forms.DateField(label="تاريخ الفحص", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    source = forms.ChoiceField(label="مصدر الفحص", choices=[("internal", "فحص داخل الفرع"), ("external", "وصفة خارجية")])
    examiner = forms.CharField(label="الفاحص أو الجهة", max_length=150, required=False)
    notes = forms.CharField(label="ملاحظات الفحص", max_length=2500, required=False, widget=forms.Textarea(attrs={"rows": 3}))
    image = forms.FileField(label="صورة فحص النظر (اختيارية)", required=False, widget=forms.FileInput(attrs={"accept": "image/jpeg,image/png"}), help_text="JPEG أو PNG حتى 5 ميجابايت. الصورة للتوثيق ولا تُحوّل إلى قياسات تلقائيًا.")
    expected_version = forms.IntegerField(widget=forms.HiddenInput, required=False, min_value=1)
    correction_reason = forms.CharField(label="سبب التصحيح", required=False, max_length=300)
    image_action = forms.ChoiceField(label="صورة الإصدار الجديد", choices=[("keep", "الإبقاء على الصورة السابقة"), ("replace", "استبدال بصورة جديدة"), ("remove", "بدون صورة في الإصدار الجديد")], required=False)

    def __init__(self, *args, actor_id, customer, correction=False, previous_image=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.correction, self.previous_image = correction, previous_image
        if not correction:
            self.fields.pop("correction_reason")
            self.fields.pop("image_action")
            self.fields["branch_id"] = forms.ModelChoiceField(label="فرع الفحص", queryset=visible_branches(actor_id, "prescription.write").filter(customerbranchaccess__customer=customer))
            self.fields["branch_id"].label_from_instance = lambda b: f"{b.name} · {b.code}"
            self.fields["branch_id"].widget.attrs.update({"class": "control", "aria-label": "فرع الفحص"})
        else:
            self.fields["correction_reason"].required = True
            self.fields["expected_version"].required = True
            self.fields["image_action"].required = True
        for eye, label in (("right", "اليمنى"), ("left", "اليسرى")):
            for part, caption in (("sphere", "SPH"), ("cylinder", "CYL"), ("axis", "AXIS"), ("add", "ADD"), ("pd", "PD")):
                low, high = RANGES[part]
                options = {"required": False, "label": f"{caption} {label}", "min_value": low, "max_value": high,
                    "widget": forms.NumberInput(attrs={"class": "control", "dir": "ltr", "step": 1 if part == "axis" else ("0.01" if part == "pd" else "0.25"), "aria-label": f"{caption} {label}"})}
                self.fields[f"{eye}_{part}"] = forms.IntegerField(**options) if part == "axis" else forms.DecimalField(decimal_places=2, max_digits=5, **options)

    def clean(self):
        data = super().clean()
        if not self.errors:
            keep = self.correction and data.get("image_action") == "keep" and self.previous_image
            validate_measurements(data, has_image=bool(data.get("image")) or keep)
        return data

    @property
    def right_fields(self):
        return [self[key] for key in MEASUREMENTS if key.startswith("right_")]

    @property
    def left_fields(self):
        return [self[key] for key in MEASUREMENTS if key.startswith("left_")]

    @property
    def general_fields(self):
        return [self[key] for key in self.fields if key not in MEASUREMENTS]
