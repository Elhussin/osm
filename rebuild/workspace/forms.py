from django import forms
from access.models import Branch
from access.policy import ROLES
from access.authorization import authorization_state, delegation_permitted
from .labels import ROLE_LABELS


class StyledForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "control")
            field.widget.attrs.setdefault("aria-label", field.label)


class BranchForm(StyledForm):
    name = forms.CharField(label="اسم الفرع", max_length=200)
    code = forms.CharField(label="رمز الفرع", max_length=30, help_text="رمز مختصر وفريد، مثل BR01.")
    kind = forms.ChoiceField(label="نوع الموقع", choices=[("store", "محل / فرع مبيعات"), ("warehouse", "مستودع")])

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()


class RoleForm(StyledForm):
    role_code = forms.ChoiceField(label="الدور")
    branch_id = forms.ModelChoiceField(label="الفرع", queryset=Branch.objects.none(), required=False, empty_label="على مستوى الشركة")

    def __init__(self, *args, actor_id, **kwargs):
        super().__init__(*args, **kwargs)
        state = authorization_state(actor_id)
        branch_ids = state[0].branch_access & state[1].active_branches if state else frozenset()
        self.fields["branch_id"].queryset = Branch.objects.filter(pk__in=branch_ids).order_by("name")
        self.fields["branch_id"].label_from_instance = lambda b: f"{b.name} ({b.code})"
        choices = [(code, ROLE_LABELS[code]) for code, role in ROLES.items() if code != "owner" and (delegation_permitted(state, role) if role.scope == "company" else any(delegation_permitted(state, role, b) for b in branch_ids))]
        self.fields["role_code"].choices = [("", "اختر الدور")] + choices
        self._state = state

    def clean(self):
        data = super().clean()
        role = ROLES.get(data.get("role_code"))
        branch = data.get("branch_id")
        if role:
            if role.scope == "branch" and branch is None:
                self.add_error("branch_id", "اختر فرعًا لهذا الدور.")
            elif role.scope == "company" and branch:
                self.add_error("branch_id", "هذا الدور يُمنح على مستوى الشركة؛ اترك الفرع فارغًا.")
            elif not delegation_permitted(self._state, role, branch.pk if branch else None):
                self.add_error("role_code", "لا يمكنك منح هذا الدور ضمن النطاق المحدد.")
        return data


class InviteForm(RoleForm):
    field_order = ["username", "email", "role_code", "branch_id"]
    username = forms.CharField(label="اسم المستخدم", max_length=150, help_text="يُستخدم لتسجيل الدخول داخل الشركة.")
    email = forms.EmailField(label="البريد الإلكتروني", help_text="تصل إليه الدعوة عند تهيئة البريد.")


class MemberForm(StyledForm):
    first_name = forms.CharField(label="الاسم الأول", max_length=150, required=False)
    last_name = forms.CharField(label="اسم العائلة", max_length=150, required=False)
    email = forms.EmailField(label="البريد الإلكتروني", required=False)


class StateForm(StyledForm):
    command = forms.ChoiceField(choices=[("activate", "تفعيل"), ("deactivate", "إيقاف")])


class BranchAccessForm(StyledForm):
    branch_id = forms.ModelChoiceField(label="الفرع", queryset=Branch.objects.filter(active=True))
    command = forms.ChoiceField(label="الإجراء", choices=[("grant", "منح وصول"), ("revoke", "سحب وصول")])


class OwnershipForm(StyledForm):
    target = forms.ChoiceField(label="المالك الجديد")
    password = forms.CharField(label="كلمة المرور الحالية", widget=forms.PasswordInput)

    def __init__(self, *args, members, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target"].choices = [("", "اختر العضو")] + [(str(m.pk), m.get_full_name() or m.username) for m in members]
