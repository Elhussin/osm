from django import forms
from django.contrib.auth import login, logout
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from access.authorization import require, visible_branches
from access.models import AuditEvent
from access.services import audit
from .authentication import authenticate_limited
from .links import consume_link


class LoginForm(forms.Form):
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
    return render(request, "identity/login.html", {"form": form}, status=400 if request.method == "POST" else 200)


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


@require_http_methods(["GET"])
def home(request):
    actor = _actor(request)
    branches = visible_branches(actor)
    return render(request, "identity/home.html", {"branches": branches})


@require_http_methods(["GET"])
def branches(request):
    rows = visible_branches(_actor(request))
    return render(request, "identity/branches.html", {"count": rows.count(), "branches": rows})


@require_http_methods(["GET"])
def events(request):
    require(_actor(request), "audit.read")
    rows = AuditEvent.objects.order_by("-created_at")[:100]
    return render(request, "identity/audit.html", {"events": rows})


@require_POST
def switch_branch(request):
    actor = _actor(request)
    try:
        branch_id = forms.UUIDField().clean(request.POST.get("branch_id", ""))
    except ValidationError:
        raise PermissionDenied from None
    branch = visible_branches(actor).filter(pk=branch_id).first()
    if branch is None:
        raise PermissionDenied
    request.session["selected_branch"] = str(branch.pk)
    return redirect("account-home")


class PasswordLinkForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput, max_length=2000)
    password = forms.CharField(widget=forms.PasswordInput, label="كلمة المرور الجديدة")


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
            return redirect("login")
    # Token is submitted in POST, not included in access-log URLs.
    return render(request, "identity/password_link.html", {"form": form}, status=400 if form.errors else 200)
