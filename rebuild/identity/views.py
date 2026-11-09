from django import forms
from django.contrib.auth import login, logout
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from access.services import audit
from .authentication import authenticate_limited
from .links import consume_link
from workspace.forms import StyledForm
from django.contrib import messages
from django.db import transaction


class LoginForm(StyledForm):
    username = forms.CharField(max_length=150, label="اسم المستخدم")
    password = forms.CharField(widget=forms.PasswordInput, label="كلمة المرور")


@require_http_methods(["GET", "POST"])
def sign_in(request):
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate_limited(request, **form.cleaned_data)
        if user:
            login(request, user)
            request.session["company_id"] = str(request.company.pk)
            audit(user.pk, "session.login")
            return redirect("account-home")
        form.add_error(None, "تعذّر تسجيل الدخول. تحقق من البيانات أو حاول لاحقًا.")
    return render(request, "identity/login.html", {"form": form, "title": "تسجيل الدخول"}, status=400 if request.method == "POST" else 200)


@require_POST
def sign_out(request):
    if request.user.is_authenticated:
        audit(request.user.pk, "session.logout")
    logout(request)
    return redirect("login")


def _actor(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    return request.user.pk


@require_POST
def switch_branch(request):
    actor = _actor(request)
    try:
        branch_id = forms.UUIDField().clean(request.POST.get("branch_id", ""))
    except ValidationError:
        raise PermissionDenied from None
    from workspace.context import ui_context
    branch = next((b for b in ui_context(request).get("user_branches", []) if b.pk == branch_id), None)
    if branch is None:
        raise PermissionDenied
    request.session["selected_branch"] = str(branch.pk)
    return redirect("account-home")


class PasswordLinkForm(StyledForm):
    token = forms.CharField(label="رمز التفعيل", widget=forms.Textarea(attrs={"rows": 3, "dir": "ltr"}), max_length=2000, help_text="يُملأ من الرابط تلقائيًا، أو يمكنك لصق الرمز الذي وصلك.")
    password = forms.CharField(widget=forms.PasswordInput, label="كلمة المرور الجديدة")
    password_confirmation = forms.CharField(widget=forms.PasswordInput, label="تأكيد كلمة المرور")

    def clean(self):
        data = super().clean()
        if data.get("password") != data.get("password_confirmation"):
            self.add_error("password_confirmation", "كلمتا المرور غير متطابقتين.")
        return data


@require_http_methods(["GET", "POST"])
def password_link(request, purpose):
    if purpose not in {"invite", "reset"}:
        raise PermissionDenied
    form = PasswordLinkForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            consume_link(form.cleaned_data["token"], purpose, form.cleaned_data["password"])
        except (PermissionDenied, ValidationError):
            form.add_error(None, "تعذّر قبول الرابط أو كلمة المرور.")
        else:
            messages.success(request, "حُفظت كلمة المرور. يمكنك تسجيل الدخول الآن.")
            return redirect("login")
    # Token is submitted in POST, not included in access-log URLs.
    return render(request, "identity/password_link.html", {"form": form, "title": "تعيين كلمة المرور"}, status=400 if form.errors else 200)


class RecoveryForm(StyledForm):
    username = forms.CharField(label="اسم المستخدم", max_length=150)


@require_http_methods(["GET", "POST"])
@transaction.atomic
def recovery(request):
    form = RecoveryForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        from .recovery import prepare_recovery
        from workspace.delivery import deliver_link
        prepared = prepare_recovery(request, form.cleaned_data["username"])
        if prepared:
            user, token = prepared
            deliver_link(request, user=user, token=token, purpose="reset", actor_id=None)
        return render(request, "identity/recovery_sent.html", {"title": "استعادة الحساب"})
    return render(request, "identity/recovery.html", {"form": form, "title": "استعادة الحساب"}, status=400 if form.errors else 200)
