from functools import wraps
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError, ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from access.authorization import require, authorization_state, delegation_permitted, allowed
from access.models import Branch, RoleAssignment, BranchAccess, AuditEvent
from access.policy import ROLES
from access import services
from identity.invitations import invite_member
from identity.links import issue_link
from .forms import BranchForm, InviteForm, MemberForm, RoleForm, StateForm, BranchAccessForm, OwnershipForm
from .labels import ROLE_LABELS, ACTION_LABELS, EVENT_LABELS
from .delivery import deliver_link


def secured(permission=None):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if permission:
                require(request.user.pk, permission)
            return view(request, *args, **kwargs)
        return wrapped
    return decorate


def page(request, template, *, title, active_page, status=200, **context):
    return render(request, template, {"title": title, "active_page": active_page, **context}, status=status)


def apply(form, operation):
    try:
        return True, operation()
    except ValidationError as exc:
        # Do not leak internal English model names/fields into the workflow.
        known = {"Cannot disable the last active owner": "لا يمكن إيقاف آخر مالك نشط للشركة.", "Accept the invitation before activating this account": "يجب قبول الدعوة وتعيين كلمة مرور قبل تفعيل الحساب."}
        form.add_error(None, next((known[m] for m in exc.messages if m in known), "تعذّر الحفظ. تحقق من البيانات ومن عدم تكرار اسم المستخدم أو رمز الفرع."))
    except IntegrityError:
        form.add_error(None, "توجد بيانات مطابقة. حدّث الصفحة وراجع المدخلات.")
    except ObjectDoesNotExist:
        form.add_error(None, "لم يعد السجل متاحًا. حدّث الصفحة وراجع الاختيار.")
    return False, None


def listing(request, rows):
    result = Paginator(rows, 20).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return {"page_obj": result, "query_params": params.urlencode(), "q": request.GET.get("q", "")[:100], "status_filter": request.GET.get("status", "")}


@require_http_methods(["GET"])
@secured()
def overview(request):
    from .context import ui_context
    ui = ui_context(request)
    context = {"branch_count": len(ui.get("user_branches", []))}
    if ui.get("can_members"):
        context.update(member_count=get_user_model().objects.count(), invited_count=get_user_model().objects.filter(is_active=False, password__startswith="!").count())
    if ui.get("can_branches"):
        context["managed_branch_count"] = Branch.objects.count()
    return page(request, "workspace/home.html", title="نظرة عامة", active_page="home", **context)


@require_http_methods(["GET"])
@secured("members.manage")
def members(request):
    rows = get_user_model().objects.all().order_by("username")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    status = request.GET.get("status")
    if status == "active":
        rows = rows.filter(is_active=True)
    elif status == "inactive":
        rows = rows.filter(is_active=False).exclude(password__startswith="!")
    elif status == "invited":
        rows = rows.filter(is_active=False, password__startswith="!")
    rows = rows.prefetch_related(Prefetch("roleassignment_set", queryset=RoleAssignment.objects.filter(active=True).select_related("branch"), to_attr="display_assignments"))
    context = listing(request, rows)
    for user in context["page_obj"]:
        for grant in user.display_assignments:
            grant.display_name = ROLE_LABELS.get(grant.role_id, "دور غير متاح")
    return page(request, "workspace/members.html", title="الأعضاء", active_page="members", **context)


@require_http_methods(["GET", "POST"])
@secured("members.manage")
@transaction.atomic
def invite(request):
    require(request.user.pk, "roles.manage")
    form = InviteForm(request.POST if request.method == "POST" else None, actor_id=request.user.pk)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        ok, result = apply(form, lambda: invite_member(request.user.pk, username=data["username"], email=data["email"], role_code=data["role_code"], branch_id=data["branch_id"].pk if data["branch_id"] else None))
        if ok:
            user, token = result
            delivery = deliver_link(request, user=user, token=token, purpose="invite", actor_id=request.user.pk)
            return page(request, "workspace/delivery.html", title="دعوة العضو", active_page="members", member=user, purpose="invite", **delivery)
    return page(request, "workspace/form.html", title="دعوة عضو جديد", active_page="members", form=form, description="أنشئ حسابًا مستقلًا للموظف، وحدد دوره ونطاق عمله.", submit_label="إنشاء الدعوة", cancel_url="members", status=422 if form.errors else 200)


def member_context(request, user, form=None, role_form=None, access_form=None):
    state = authorization_state(request.user.pk)
    grants = list(RoleAssignment.objects.filter(user=user, active=True).select_related("branch").order_by("role_id"))
    for grant in grants:
        grant.display_name = ROLE_LABELS.get(grant.role_id, "دور غير متاح")
        grant.can_revoke = grant.role_id != "owner" and allowed(request.user.pk, "roles.manage") and delegation_permitted(state, ROLES[grant.role_id], grant.branch_id)
    editable = all(delegation_permitted(state, ROLES[g.role_id], g.branch_id) for g in grants)
    return {"member": user, "grants": grants, "editable": editable, "form": form or MemberForm(initial={"first_name": user.first_name, "last_name": user.last_name, "email": user.email}), "role_form": role_form or RoleForm(actor_id=request.user.pk), "access_form": access_form or BranchAccessForm(), "branch_links": BranchAccess.objects.filter(user=user, active=True).select_related("branch")}


@require_http_methods(["GET", "POST"])
@secured("members.manage")
def member_detail(request, member_id):
    user = get_object_or_404(get_user_model(), pk=member_id)
    form = None
    if request.method == "POST":
        form = MemberForm(request.POST)
        if form.is_valid():
            ok, _ = apply(form, lambda: services.update_member(request.user.pk, user_id=user.pk, **form.cleaned_data))
            if ok:
                messages.success(request, "حُفظت بيانات العضو.")
                return redirect("member-detail", member_id=user.pk)
    return page(request, "workspace/member.html", title=user.get_full_name() or user.username, active_page="members", status=422 if form is not None and form.errors else 200, **member_context(request, user, form=form))


@require_POST
@secured("members.manage")
def member_state(request, member_id):
    user = get_object_or_404(get_user_model(), pk=member_id)
    form = StateForm(request.POST)
    if form.is_valid():
        ok, _ = apply(form, lambda: services.set_member_active(request.user.pk, user_id=user.pk, active=form.cleaned_data["command"] == "activate"))
        if ok:
            messages.success(request, "حُدّثت حالة العضو.")
            return redirect("member-detail", member_id=user.pk)
    return page(request, "workspace/action_error.html", title="تعذّر تغيير حالة العضو", active_page="members", form=form, status=422, back_url="members")


@require_POST
@secured("roles.manage")
def member_role(request, member_id):
    user = get_object_or_404(get_user_model(), pk=member_id)
    require(request.user.pk, "members.manage")
    form = RoleForm(request.POST, actor_id=request.user.pk)
    if form.is_valid():
        data = form.cleaned_data
        ok, _ = apply(form, lambda: services.assign_role(request.user.pk, user_id=user.pk, role_code=data["role_code"], branch_id=data["branch_id"].pk if data["branch_id"] else None))
        if ok:
            messages.success(request, "أُسند الدور ضمن النطاق المحدد.")
            return redirect("member-detail", member_id=user.pk)
    return page(request, "workspace/member.html", title=user.username, active_page="members", status=422, **member_context(request, user, role_form=form))


@require_POST
@secured("roles.manage")
def revoke_assignment(request, member_id, assignment_id):
    require(request.user.pk, "members.manage")
    get_object_or_404(RoleAssignment, pk=assignment_id, user_id=member_id)
    services.revoke_role(request.user.pk, assignment_id=assignment_id)
    messages.success(request, "سُحب الدور من العضو.")
    return redirect("member-detail", member_id=member_id)


@require_POST
@secured("ownership.transfer")
def member_branch_access(request, member_id):
    user = get_object_or_404(get_user_model(), pk=member_id)
    form = BranchAccessForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        operation = services.grant_branch_access if data["command"] == "grant" else services.revoke_branch_access
        ok, _ = apply(form, lambda: operation(request.user.pk, user_id=user.pk, branch_id=data["branch_id"].pk))
        if ok:
            messages.success(request, "حُدّث وصول العضو إلى الفرع.")
            return redirect("member-detail", member_id=user.pk)
    return page(request, "workspace/member.html", title=user.username, active_page="members", status=422, **member_context(request, user, access_form=form))


@require_POST
@secured("members.manage")
@transaction.atomic
def resend_link(request, member_id, purpose):
    user = get_object_or_404(get_user_model(), pk=member_id)
    token = issue_link(request.user.pk, user.pk, purpose)
    delivery = deliver_link(request, user=user, token=token, purpose=purpose, actor_id=request.user.pk)
    return page(request, "workspace/delivery.html", title="رابط الحساب", active_page="members", member=user, purpose=purpose, **delivery)


@require_http_methods(["GET"])
@secured()
def branches(request):
    from .context import ui_context
    ui = ui_context(request)
    rows = Branch.objects.all() if ui.get("can_branches") else Branch.objects.filter(pk__in=[b.pk for b in ui.get("user_branches", [])])
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(name__icontains=q) | Q(code__icontains=q))
    status = request.GET.get("status")
    if status in {"active", "inactive"}:
        rows = rows.filter(active=status == "active")
    context = listing(request, rows.order_by("code"))
    context["count"] = context["page_obj"].paginator.count
    return page(request, "workspace/branches.html", title="الفروع والمستودعات", active_page="branches", **context)


@require_http_methods(["GET", "POST"])
@secured("branches.manage")
def branch_form(request, branch_id=None):
    branch = get_object_or_404(Branch, pk=branch_id) if branch_id else None
    initial = {"name": branch.name, "code": branch.code, "kind": branch.kind} if branch else None
    form = BranchForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        operation = lambda: services.update_branch(request.user.pk, branch_id=branch.pk, **form.cleaned_data) if branch else services.create_branch(request.user.pk, **form.cleaned_data)
        ok, _ = apply(form, operation)
        if ok:
            messages.success(request, "حُفظت بيانات الفرع.")
            return redirect("account-branches")
    return page(request, "workspace/form.html", title="تعديل الفرع" if branch else "إضافة فرع", active_page="branches", form=form, submit_label="حفظ الفرع", cancel_url="account-branches", status=422 if form.errors else 200)


@require_POST
@secured("branches.manage")
def branch_state(request, branch_id):
    branch = get_object_or_404(Branch, pk=branch_id)
    form = StateForm(request.POST)
    if form.is_valid():
        ok, _ = apply(form, lambda: services.set_branch_active(request.user.pk, branch_id=branch.pk, active=form.cleaned_data["command"] == "activate"))
        if ok:
            messages.success(request, "حُدّثت حالة الفرع.")
            return redirect("account-branches")
    return page(request, "workspace/action_error.html", title="تعذّر تغيير حالة الفرع", active_page="branches", form=form, back_url="account-branches", status=422)


@require_http_methods(["GET"])
@secured("roles.manage")
def roles(request):
    rows = [{"code": code, "label": ROLE_LABELS[code], "scope": "الشركة" if role.scope == "company" else "فرع محدد", "permissions": [ACTION_LABELS[p] for p in sorted(role.permissions)]} for code, role in ROLES.items()]
    return page(request, "workspace/roles.html", title="الأدوار والصلاحيات", active_page="roles", roles=rows)


@require_http_methods(["GET"])
@secured("audit.read")
def events(request):
    rows = AuditEvent.objects.order_by("-created_at", "id")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        codes = [code for code, label in EVENT_LABELS.items() if q in label]
        rows = rows.filter(action__in=codes)
    context = listing(request, rows)
    actors = {m.pk: m.get_full_name() or m.username for m in get_user_model().objects.filter(pk__in={e.actor_id for e in context["page_obj"] if e.actor_id})}
    for event in context["page_obj"]:
        event.display_action = EVENT_LABELS.get(event.action, "حدث إداري")
        event.actor_name = actors.get(event.actor_id, "عضو غير متاح") if event.actor_id else "النظام"
    return page(request, "workspace/audit.html", title="سجل التدقيق", active_page="audit", **context)


@require_http_methods(["GET", "POST"])
@secured("ownership.transfer")
def ownership(request):
    members = get_user_model().objects.filter(is_active=True).exclude(pk=request.user.pk).order_by("username")
    form = OwnershipForm(request.POST if request.method == "POST" else None, members=members)
    if request.method == "POST" and form.is_valid():
        try:
            services.transfer_ownership(request.user.pk, new_owner_id=form.cleaned_data["target"], password=form.cleaned_data["password"])
        except PermissionDenied:
            require(request.user.pk, "ownership.transfer")
            form.add_error("password", "تعذّر التحقق من كلمة المرور الحالية.")
        except ObjectDoesNotExist:
            form.add_error("target", "لم يعد العضو متاحًا. حدّث الصفحة.")
        else:
            messages.success(request, "نُقلت ملكية الشركة إلى العضو المختار.")
            return redirect("account-home")
    return page(request, "workspace/form.html", title="نقل ملكية الشركة", active_page="ownership", form=form, description="يصبح العضو المختار مالك الشركة وتُسحب صفة المالك من حسابك. تبقى الأدوار الأخرى كما هي.", submit_label="نقل الملكية", cancel_url="account-home", status=422 if form.errors else 200)


def error_page(request, exception=None, status=403):
    titles = {400: "تعذّر قبول البيانات أو حجم المرفق", 403: "لا تملك صلاحية لهذا الإجراء", 404: "الصفحة غير موجودة", 500: "تعذّر إكمال الطلب"}
    return render(request, "workspace/error.html", {"title": titles[status], "error_status": status}, status=status)
