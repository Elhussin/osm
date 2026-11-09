import uuid
from django.contrib import messages
from django.core.exceptions import ValidationError, ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from access.authorization import allowed, visible_branches
from workspace.views import secured, page, listing
from .models import Product, Variant, PriceRule, KINDS
from .forms import ProductForm, ProductEditForm, VariantForm, VariantEditForm, RuleForm, QuoteForm
from .specifications import display_specs
from . import services


def attempt(form, operation):
    try:
        return operation()
    except ValidationError as exc:
        if hasattr(exc, "message_dict"):
            for key, errors in exc.message_dict.items():
                if any(getattr(error, "code", None) == "unique" for error in exc.error_dict.get(key, [])):
                    errors = ["توجد بيانات مطابقة. راجع رمز المنتج أو SKU أو الباركود أو مواصفات المتغير."]
                field = key if key in form.fields else ("spec_" + key if "spec_" + key in form.fields else None)
                form.add_error(field, errors)
        else:
            form.add_error(None, exc)
    except IntegrityError:
        form.add_error(None, "توجد بيانات مطابقة أو عملية متزامنة. حدّث الصفحة وراجع المدخلات.")
    except ObjectDoesNotExist:
        form.add_error(None, "السجل غير متاح أو موقوف. حدّث الصفحة.")
    return None


@require_http_methods(["GET"])
@secured("catalog.read")
def products(request):
    rows = Product.objects.annotate(variant_count=Count("variants", distinct=True)).order_by("name", "id")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(brand__icontains=q) | Q(model__icontains=q) | Q(variants__sku__icontains=q) | Q(variants__barcode__icontains=q)).distinct()
    kind = request.GET.get("kind", "")
    if kind in dict(KINDS):
        rows = rows.filter(kind=kind)
    if request.GET.get("status") in {"active", "inactive"}:
        rows = rows.filter(active=request.GET["status"] == "active")
    return page(request, "catalog/products.html", title="دليل المنتجات", active_page="catalog", kinds=KINDS, kind_filter=kind, **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured("catalog.manage")
def product_new(request):
    form = ProductForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        product = attempt(form, lambda: services.create_product(request.user.pk, **form.cleaned_data))
        if product:
            messages.success(request, "أُضيف المنتج. أضف متغيراته القابلة للبيع.")
            return redirect("product-detail", product_id=product.pk)
    return page(request, "catalog/form.html", title="إضافة منتج", active_page="catalog", form=form, status=422 if form.errors else 200)


@require_http_methods(["GET", "POST"])
@secured("catalog.manage")
def product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductEditForm(request.POST if request.method == "POST" else None, initial={"name": product.name, "brand": product.brand, "model": product.model, "active": str(product.active).lower(), "expected_version": product.version})
    if request.method == "POST" and form.is_valid():
        result = attempt(form, lambda: services.update_product(request.user.pk, product_id=product.pk, **form.cleaned_data))
        if result:
            messages.success(request, "حُفظ المنتج.")
            return redirect("product-detail", product_id=product.pk)
    return page(request, "catalog/form.html", title="تعديل المنتج", active_page="catalog", form=form, product=product, status=422 if form.errors else 200)


@require_http_methods(["GET"])
@secured("catalog.read")
def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    rows = product.variants.select_related("product").order_by("sku", "id")
    q = request.GET.get("q", "")[:100].strip()
    if q:
        rows = rows.filter(Q(sku__icontains=q) | Q(barcode__icontains=q))
    return page(request, "catalog/product.html", title=product.name, active_page="catalog", product=product, **listing(request, rows))


@require_http_methods(["GET", "POST"])
@secured("catalog.manage")
def variant_new(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)
    default_unit = "box" if product.kind == "contact_lens" else ("service" if product.kind == "service" else "piece")
    form = VariantForm(request.POST if request.method == "POST" else None, kind=product.kind, initial={"sku": product.code + "-" + uuid.uuid4().hex[:8].upper(), "unit": default_unit})
    if request.method == "POST" and form.is_valid():
        data = {key: form.cleaned_data[key] for key in ("sku", "barcode", "unit", "base_price")}
        variant = attempt(form, lambda: services.create_variant(request.user.pk, product_id=product.pk, specifications=form.specifications(), **data))
        if variant:
            messages.success(request, "أُضيف المتغير بمواصفات ووحدة بيع ثابتتين.")
            return redirect("variant-detail", variant_id=variant.pk)
    return page(request, "catalog/form.html", title="إضافة متغير: " + product.get_kind_display(), active_page="catalog", form=form, product=product, variant_creation=True, status=422 if form.errors else 200)


@require_http_methods(["GET"])
@secured("catalog.read")
def variant_detail(request, variant_id):
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=variant_id)
    rules = services.price_rules_for(request.user.pk, variant) if allowed(request.user.pk, "catalog.manage") else PriceRule.objects.none()
    return page(request, "catalog/variant.html", title=variant.sku, active_page="catalog", variant=variant, specifications=display_specs(variant), can_quote=visible_branches(request.user.pk, "invoice.read").exists(), **listing(request, rules))


@require_http_methods(["GET", "POST"])
@secured("catalog.manage")
def variant_edit(request, variant_id):
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=variant_id)
    form = VariantEditForm(request.POST if request.method == "POST" else None, initial={"base_price": variant.base_price, "active": str(variant.active).lower(), "expected_version": variant.version})
    if request.method == "POST" and form.is_valid():
        result = attempt(form, lambda: services.update_variant(request.user.pk, variant_id=variant.pk, **form.cleaned_data))
        if result:
            messages.success(request, "حُدّث السعر الأساسي وحالة المتغير.")
            return redirect("variant-detail", variant_id=variant.pk)
    return page(request, "catalog/form.html", title="تحديث سعر المتغير وحالته", active_page="catalog", form=form, product=variant.product, variant=variant, status=422 if form.errors else 200)


def scoped_form(request, form_type, *, quoting=False):
    refreshing = request.method == "POST" and request.POST.get("refresh") == "customers"
    initial = {"valid_from": timezone.localdate(), "as_of": timezone.localdate(), "channel": "retail", "min_quantity": 1, "count": 1, "branch_id": request.session.get("selected_branch")}
    if refreshing:
        initial.update(request.POST.dict())
    data = request.POST if request.method == "POST" and not refreshing else None
    branch_id = request.POST.get("branch_id") if request.method == "POST" else initial.get("branch_id")
    form = form_type(data, actor_id=request.user.pk, branch_id=branch_id, quoting=quoting, initial=initial)
    return form, refreshing


@require_http_methods(["GET", "POST"])
@secured("catalog.manage")
def rule_new(request, variant_id):
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=variant_id, active=True, product__active=True)
    form, refreshing = scoped_form(request, RuleForm)
    if request.method == "POST" and not refreshing and form.is_valid():
        data = form.cleaned_data.copy()
        data["branch_id"] = data["branch_id"].pk if data["branch_id"] else None
        data["customer_id"] = data["customer_id"].pk if data["customer_id"] else None
        result = attempt(form, lambda: services.create_price_rule(request.user.pk, variant_id=variant.pk, **data))
        if result:
            messages.success(request, "أُضيفت قاعدة السعر.")
            return redirect("variant-detail", variant_id=variant.pk)
    return page(request, "catalog/form.html", title="إضافة قاعدة سعر", active_page="catalog", form=form, product=variant.product, variant=variant, scope_form=True, status=422 if form.errors else 200)


@require_POST
@secured("catalog.manage")
def rule_disable(request, rule_id):
    rule = get_object_or_404(PriceRule, pk=rule_id)
    services.disable_price_rule(request.user.pk, rule_id=rule.pk)
    messages.success(request, "أوقفت القاعدة مع الاحتفاظ بسجلها.")
    return redirect("variant-detail", variant_id=rule.variant_id)


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def price_preview(request, variant_id):
    if not visible_branches(request.user.pk, "invoice.read").exists():
        raise PermissionDenied
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=variant_id)
    form, refreshing = scoped_form(request, QuoteForm, quoting=True)
    quote = None
    if request.method == "POST" and not refreshing and form.is_valid():
        data = form.cleaned_data.copy()
        data["branch_id"] = data["branch_id"].pk
        data["customer_id"] = data["customer_id"].pk if data["customer_id"] else None
        quote = attempt(form, lambda: services.quote_price(request.user.pk, variant_id=variant.pk, **data))
    return page(request, "catalog/quote.html", title="معاينة السعر", active_page="catalog", form=form, variant=variant, quote=quote, status=422 if form.errors else 200)
