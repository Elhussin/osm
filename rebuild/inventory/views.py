import uuid
from django.contrib import messages
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError, ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods, require_POST
from access.authorization import allowed, visible_branches
from catalog.models import Product, Variant
from workspace.views import secured, page, listing
from .models import StockBalance, StockReceipt
from .forms import MatrixFilterForm, MatrixEntryForm, ReverseForm, ConfirmForm, families, family_label
from .matrix import number, label
from . import services

SALT = "inventory.matrix.preview.v1"


def attempt(form, operation):
    try:
        return operation()
    except ValidationError as exc:
        form.add_error(None, " ".join(exc.messages))
    except (IntegrityError, ObjectDoesNotExist):
        form.add_error(None, "تغيرت بيانات الصنف أو المتغير. حدّث المصفوفة وأعد المعاينة؛ لم يُحفظ أثر جزئي.")
    return None


@require_http_methods(["GET"])
@secured("catalog.read")
def lens_products(request):
    if not visible_branches(request.user.pk, "stock.read").exists():
        raise PermissionDenied
    rows = Product.objects.filter(kind="stock_lens").order_by("name", "id")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(brand__icontains=q))
    return page(request, "inventory/products.html", title="مخزون العدسات بالمصفوفة", active_page="inventory", **listing(request, rows))


def posted_cells(data, rows, columns):
    permitted = {f"q_{i}_{j}" for i in range(len(rows)) for j in range(len(columns))}
    if any(key.startswith("q_") and (key not in permitted or len(data.getlist(key)) != 1) for key in data):
        raise ValidationError("حقول كمية مكررة أو خارج النطاق المعروض.")
    return [{"sphere": number(sphere), "cylinder": number(cylinder), "quantity": data[f"q_{i}_{j}"].strip()}
        for i, sphere in enumerate(rows) for j, cylinder in enumerate(columns) if data.get(f"q_{i}_{j}", "").strip()]


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def lens_matrix(request, product_id):
    branches = visible_branches(request.user.pk, "stock.read")
    if not branches.exists():
        raise PermissionDenied
    product = get_object_or_404(Product, pk=product_id, kind="stock_lens")
    first = families(product).first()
    selected = next((b for b in branches if str(b.pk) == request.session.get("selected_branch")), None) or branches.first()
    defaults = {"branch_id": str(selected.pk), "template_id": str(first.pk) if first else "", "sphere_min": "-2", "sphere_max": "2", "cylinder_min": "-2", "cylinder_max": "0"}
    submitted = request.POST if request.method == "POST" else request.GET
    defaults.update({key: submitted[key] for key in defaults if key in submitted})
    filters = MatrixFilterForm(defaults, actor_id=request.user.pk, product=product)
    entry = MatrixEntryForm(request.POST if request.method == "POST" else None, initial={"operation_key": uuid.uuid4(), "template_version": first.version if first else 1})
    can_create = allowed(request.user.pk, "catalog.manage")
    if not can_create:
        from django import forms
        entry.fields["create_missing"].widget = forms.HiddenInput()
    context = {"product": product, "filters": filters, "entry_form": entry, "has_families": first is not None, "can_create": can_create}
    if first and filters.is_valid():
        branch, template = filters.cleaned_data["branch_id"], filters.cleaned_data["template_id"]
        rows, columns = filters.matrix_axes
        can_receive = product.active and template.active and allowed(request.user.pk, "stock.receive", [branch.pk])
        if request.method == "GET":
            entry.initial["template_version"] = template.version
        variants = list(Variant.objects.filter(product=product, matrix_family=template.matrix_family, sphere__in=rows, cylinder__in=columns))
        by_coordinate = {(variant.sphere, variant.cylinder): variant for variant in variants}
        balances = {b.variant_id: b for b in StockBalance.objects.filter(branch=branch, variant_id__in=[v.pk for v in variants])}
        table = []
        for i, sphere in enumerate(rows):
            cells = []
            for j, cylinder in enumerate(columns):
                variant = by_coordinate.get((sphere, cylinder))
                balance = balances.get(variant.pk) if variant else None
                cells.append({"name": f"q_{i}_{j}", "row": i, "column": j, "sphere": label(sphere), "cylinder": label(cylinder), "variant": variant,
                    "on_hand": balance.on_hand if balance else 0, "reserved": balance.reserved if balance else 0, "available": balance.available if balance else 0,
                    "editable": can_receive and ((variant is not None and variant.active) or (variant is None and can_create)), "value": submitted.get(f"q_{i}_{j}", "") if request.method == "POST" else ""})
            table.append({"label": label(sphere), "cells": cells})
        totals = StockBalance.objects.filter(branch=branch, variant__product=product, variant__matrix_family=template.matrix_family).aggregate(on_hand=Sum("on_hand"), reserved=Sum("reserved"))
        context.update(branch=branch, lens_template=template, family_label=family_label(template), columns=[label(value) for value in columns], rows=table, can_receive=can_receive,
            family_on_hand=totals["on_hand"] or 0, family_reserved=totals["reserved"] or 0, family_available=(totals["on_hand"] or 0) - (totals["reserved"] or 0))
        if request.method == "POST":
            if not can_receive:
                raise PermissionDenied
            if request.POST.get("command") != "edit" and entry.is_valid():
                def preview():
                    return services.preview_receipt(request.user.pk, product_id=product.pk, template_id=template.pk, branch_id=branch.pk, cells=posted_cells(request.POST, rows, columns), **entry.cleaned_data)
                result = attempt(entry, preview)
                if result:
                    token = signing.dumps(result["payload"], salt=SALT, compress=True)
                    known = set(filters.fields) | set(entry.fields)
                    edit_data = [{"name": key, "value": value} for key, value in request.POST.items() if key in known or key.startswith("q_")]
                    return page(request, "inventory/preview.html", title="مراجعة إضافة المخزون", active_page="inventory", product=product, branch=branch, preview=result, edit_data=edit_data, confirm_form=ConfirmForm(initial={"preview_token": token}))
    status = 422 if (first and (filters.errors or entry.errors)) else 200
    return page(request, "inventory/matrix.html", title="مصفوفة مخزون العدسات", active_page="inventory", status=status, **context)


@require_POST
@secured("catalog.read")
def confirm_receipt(request):
    form = ConfirmForm(request.POST)
    if form.is_valid():
        def commit():
            try:
                payload = signing.loads(form.cleaned_data["preview_token"], salt=SALT, max_age=900)
                if payload.pop("company_id") != str(request.company.pk) or payload.pop("actor_id") != str(request.user.pk):
                    raise PermissionDenied
            except (signing.BadSignature, ValueError, KeyError, TypeError):
                raise ValidationError("المعاينة غير صالحة أو انتهت مدتها. أعد فتح المصفوفة.") from None
            return services.receive_matrix(request.user.pk, **payload)
        document = attempt(form, commit)
        if document:
            messages.success(request, "اعتمدت إضافة المخزون. إعادة إرسال الطلب نفسه لا تكرر الكميات.")
            return redirect("stock-receipt", receipt_id=document.pk)
    return page(request, "inventory/error.html", title="تعذّر اعتماد المخزون", active_page="inventory", form=form, status=422)


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def receipt_detail(request, receipt_id):
    document = get_object_or_404(services.receipts_for(request.user.pk).select_related("branch", "created_by", "reverses"), pk=receipt_id)
    reversal = StockReceipt.objects.filter(reverses=document).first()
    can_reverse = document.kind == "receipt" and reversal is None and allowed(request.user.pk, "stock.reverse", [document.branch_id])
    form = ReverseForm(request.POST if request.method == "POST" else None, initial={"operation_key": uuid.uuid4()})
    if request.method == "POST":
        if document.kind != "receipt":
            raise PermissionDenied
        if form.is_valid():
            result = attempt(form, lambda: services.reverse_receipt(request.user.pk, receipt_id=document.pk, **form.cleaned_data))
            if result:
                messages.success(request, "عُكست إضافة المخزون بمستند مستقل.")
                return redirect("stock-receipt", receipt_id=result.pk)
    return page(request, "inventory/receipt.html", title=document.get_kind_display(), active_page="inventory", document=document, reversal=reversal, movements=document.movements.select_related("variant").order_by("id"), form=form, can_reverse=can_reverse, status=422 if form.errors else 200)
