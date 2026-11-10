import uuid
from decimal import Decimal, localcontext
from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, OuterRef, Subquery
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods, require_POST
from access.models import Branch
from access.authorization import visible_branches, allowed, require
from workspace.forms import StyledForm
from workspace.views import secured, page, listing
from .models import JournalDraft, JournalRevision
from .journals import drafts_for, entries_for, save_journal_draft, act_on_journal_draft, reverse_journal
from .setup_views import attempt


class DraftForm(StyledForm):
    branch_id = forms.ModelChoiceField(label="فرع القيد", queryset=Branch.objects.none())
    entry_date = forms.DateField(label="تاريخ القيد", widget=forms.DateInput(attrs={"type": "date"}))
    reference = forms.CharField(label="المرجع (اختياري)", max_length=100, required=False)
    description = forms.CharField(label="بيان القيد", max_length=300)
    reason = forms.CharField(label="سبب حفظ الإصدار", max_length=300)
    expected_version = forms.IntegerField(widget=forms.HiddenInput, min_value=1, required=False)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, actor_id, draft=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch_id"].queryset = visible_branches(actor_id, "ledger.post").filter(pk__in=visible_branches(actor_id, "ledger.read"))
        if draft:
            del self.fields["branch_id"]
            self.fields["expected_version"].required = True


class LineForm(StyledForm):
    account_code = forms.CharField(label="رمز الحساب", max_length=30)
    debit = forms.DecimalField(label="مدين", max_digits=18, decimal_places=2, min_value=0, required=False)
    credit = forms.DecimalField(label="دائن", max_digits=18, decimal_places=2, min_value=0, required=False)
    description = forms.CharField(label="بيان السطر (اختياري)", max_length=300, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        suffix = (self.prefix or "").rsplit("-", 1)[-1]
        if suffix.isdigit():
            for field in self.fields.values():
                field.widget.attrs["aria-label"] = f"{field.label} — السطر {int(suffix) + 1}"


Lines = forms.formset_factory(LineForm, extra=0, min_num=2, validate_min=True, max_num=40, validate_max=True, absolute_max=40)


class DraftActionForm(StyledForm):
    action = forms.ChoiceField(widget=forms.HiddenInput, choices=[("post", "ترحيل"), ("cancel", "إلغاء")])
    expected_version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)
    reason = forms.CharField(label="سبب الترحيل", max_length=300)


class ReverseForm(StyledForm):
    entry_date = forms.DateField(label="تاريخ القيد العكسي", widget=forms.DateInput(attrs={"type": "date"}))
    reason = forms.CharField(label="سبب العكس", max_length=300)
    operation_key = forms.UUIDField(widget=forms.HiddenInput)


def operation_history(request, queryset):
    return Paginator(queryset.select_related("created_by").order_by("-created_at", "id"), 20).get_page(request.GET.get("history_page"))


@require_http_methods(["GET"])
@secured("ledger.read")
def journal_list(request):
    latest = JournalRevision.objects.filter(draft_id=OuterRef("pk")).order_by("-version")
    drafts = drafts_for(request.user.pk).select_related("branch").annotate(latest_description=Subquery(latest.values("description")[:1]), latest_reference=Subquery(latest.values("reference")[:1])).order_by("-created_at", "id")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        drafts = drafts.filter(Q(latest_description__icontains=q) | Q(latest_reference__icontains=q))
    if request.GET.get("status") in {"draft", "posted", "cancelled"}:
        drafts = drafts.filter(state=request.GET["status"])
    can_new = visible_branches(request.user.pk, "ledger.post").filter(pk__in=visible_branches(request.user.pk, "ledger.read")).exists()
    return page(request, "finance/journals.html", title="مسودات القيود", active_page="ledger", can_new=can_new, **listing(request, drafts))


@require_http_methods(["GET", "POST"])
@secured("ledger.read")
def draft_edit(request, draft_id=None):
    require(request.user.pk, "ledger.post")
    draft = get_object_or_404(drafts_for(request.user.pk).select_related("branch"), pk=draft_id) if draft_id else None
    if draft:
        require(request.user.pk, "ledger.post", [draft.branch_id])
        if draft.state != "draft":
            raise Http404
    elif not visible_branches(request.user.pk, "ledger.post").filter(pk__in=visible_branches(request.user.pk, "ledger.read")).exists():
        raise PermissionDenied
    revision = draft.revisions.order_by("-version").first() if draft else None
    initial = {"operation_key": uuid.uuid4(), "expected_version": draft.version if draft else None}
    if revision:
        initial.update(entry_date=revision.entry_date, reference=revision.reference, description=revision.description)
    line_initial = revision.lines if revision else None
    if request.method == "POST" and request.POST.get("command") == "add_line":
        try:
            total = int(request.POST.get("lines-TOTAL_FORMS", "0"))
            if not 2 <= total <= 40:
                raise ValueError
        except ValueError:
            return HttpResponseBadRequest("عدد أسطر غير صالح")
        initial = {name: request.POST.get(name, "") for name in DraftForm.base_fields}
        line_initial = [{name: request.POST.get(f"lines-{index}-{name}", "") for name in LineForm.base_fields} for index in range(total)]
        if total < 40:
            line_initial.append({})
        else:
            messages.error(request, "الحد الأقصى40 سطرًا.")
        form = DraftForm(actor_id=request.user.pk, draft=draft, initial=initial)
        lines = Lines(initial=line_initial, prefix="lines")
    else:
        bound = request.POST if request.method == "POST" else None
        form = DraftForm(bound, actor_id=request.user.pk, draft=draft, initial=initial)
        lines = Lines(bound, initial=line_initial, prefix="lines")
        if request.method == "POST" and form.is_valid() and lines.is_valid():
            values = dict(form.cleaned_data)
            branch = values.pop("branch_id", None)
            rows = [{"account_code": row["account_code"], "debit": row.get("debit") or Decimal("0"), "credit": row.get("credit") or Decimal("0"), "description": row.get("description", "")} for row in lines.cleaned_data if row]
            result = attempt(form, lambda: save_journal_draft(request.user.pk, draft_id=draft.pk if draft else None, branch_id=branch.pk if branch else None, lines=rows, **values))
            if result:
                return redirect("journal-draft", draft_id=result.draft_id)
    return page(request, "finance/journal_form.html", title="تعديل مسودة قيد" if draft else "مسودة قيد جديدة", active_page="ledger", form=form, lines=lines, draft=draft,
        status=422 if form.errors or lines.errors or lines.non_form_errors() else 200)


@require_http_methods(["GET", "POST"])
@secured("ledger.read")
def draft_detail(request, draft_id):
    draft = get_object_or_404(drafts_for(request.user.pk).select_related("branch"), pk=draft_id)
    revision = draft.revisions.order_by("-version").first()
    is_cancel = request.method == "POST" and "cancel-action" in request.POST
    form = DraftActionForm(request.POST if request.method == "POST" and not is_cancel else None, initial={"action": "post", "expected_version": draft.version, "operation_key": uuid.uuid4()})
    cancel_form = DraftActionForm(request.POST if is_cancel else None, prefix="cancel", initial={"action": "cancel", "expected_version": draft.version, "operation_key": uuid.uuid4()})
    cancel_form.fields["reason"].label = "سبب إلغاء المسودة"
    cancel_form.fields["reason"].widget.attrs["aria-label"] = "سبب إلغاء المسودة"
    if request.method == "POST":
        require(request.user.pk, "ledger.post", [draft.branch_id])
        submitted = cancel_form if is_cancel else form
        if submitted.is_valid():
            result = attempt(submitted, lambda: act_on_journal_draft(request.user.pk, draft_id=draft.pk, **submitted.cleaned_data))
            if result:
                return redirect("journal-entry", entry_id=result.entry_id) if result.entry_id else redirect("journal-draft", draft_id=draft.pk)
    with localcontext() as ctx:
        ctx.prec = 40
        difference = revision.total_debit - revision.total_credit if revision else Decimal("0")
    entry = getattr(draft, "posted_entry", None)
    can_edit = draft.state == "draft" and allowed(request.user.pk, "ledger.post", [draft.branch_id])
    return page(request, "finance/journal_draft.html", title="مسودة قيد", active_page="ledger", draft=draft, revision=revision, difference=difference,
        entry=entry, form=form, cancel_form=cancel_form, can_edit=can_edit, operation_page=operation_history(request, draft.operations.all()), status=422 if form.errors or cancel_form.errors else 200,
        **listing(request, draft.revisions.order_by("-version")))


@require_http_methods(["GET"])
@secured("ledger.read")
def revision_detail(request, draft_id, version):
    draft = get_object_or_404(drafts_for(request.user.pk).select_related("branch"), pk=draft_id)
    revision = get_object_or_404(draft.revisions, version=version)
    return page(request, "finance/journal_revision.html", title="إصدار مسودة محفوظ", active_page="ledger", draft=draft, revision=revision)


@require_http_methods(["GET"])
@secured("ledger.read")
def entries(request):
    rows = entries_for(request.user.pk).select_related("branch").order_by("-number")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        search = Q(reference__icontains=q) | Q(description__icontains=q)
        number = q.upper().removeprefix("JE-")
        if number.isascii() and number.isdigit() and len(number) <= 19 and int(number) <= 9223372036854775807:
            search |= Q(number=int(number))
        rows = rows.filter(search)
    return page(request, "finance/journal_entries.html", title="القيود المرحّلة", active_page="ledger", **listing(request, rows))


@require_http_methods(["GET"])
@secured("ledger.read")
def entry_detail(request, entry_id):
    entry = get_object_or_404(entries_for(request.user.pk).select_related("branch", "period", "reverses"), pk=entry_id)
    reversal = entries_for(request.user.pk).filter(reverses=entry).first()
    form = ReverseForm(initial={"operation_key": uuid.uuid4()})
    can_reverse = not entry.reverses_id and reversal is None and allowed(request.user.pk, "ledger.post", [entry.branch_id])
    return page(request, "finance/journal_entry.html", title=entry.display_number, active_page="ledger", entry=entry, rows=entry.lines.order_by("position"), form=form, reversal=reversal, can_reverse=can_reverse, operation_page=operation_history(request, entry.operations.all()))


@require_POST
@secured("ledger.read")
def entry_reverse(request, entry_id):
    entry = get_object_or_404(entries_for(request.user.pk).select_related("branch", "period"), pk=entry_id)
    require(request.user.pk, "ledger.post", [entry.branch_id])
    form = ReverseForm(request.POST)
    if form.is_valid():
        result = attempt(form, lambda: reverse_journal(request.user.pk, entry_id=entry.pk, **form.cleaned_data))
        if result:
            return redirect("journal-entry", entry_id=result.entry_id)
    return page(request, "finance/journal_entry.html", title=entry.display_number, active_page="ledger", entry=entry, rows=entry.lines.order_by("position"), form=form, can_reverse=True, status=422, operation_page=operation_history(request, entry.operations.all()))
