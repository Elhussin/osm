from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from catalog.models import Variant
from workspace.forms import StyledForm
from workspace.views import secured, page
from .labels import label_preview


class LabelForm(StyledForm):
    copies = forms.IntegerField(label="عدد الملصقات", min_value=1, max_value=120, initial=1)
    layout = forms.ChoiceField(label="قالب الطباعة", choices=[("auto", "اختيار تلقائي حسب طول الرمز"),
        ("standard", "A4 عمودي · 90×43 ملم"), ("wide", "A4 أفقي · 270×43 ملم")], initial="auto")


@require_http_methods(["GET", "POST"])
@secured("catalog.read")
def labels(request, variant_id):
    variant = get_object_or_404(Variant.objects.select_related("product"), pk=variant_id, active=True, product__active=True,
        product__kind__in=["frame", "stock_lens", "contact_lens", "accessory", "device"])
    form = LabelForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            preview = label_preview(request.user.pk, variant_id=variant.pk, **form.cleaned_data)
        except ValidationError as exc:
            form.add_error(None, " ".join(exc.messages))
        except Variant.DoesNotExist:
            form.add_error(None, "لم يعد المتغير نشطًا ومتاحًا للطباعة. حدّث الصفحة.")
        else:
            return render(request, "inventory/label_print.html", preview)
    return page(request, "inventory/label_form.html", title="ملصقات الباركود", active_page="catalog", variant=variant,
        form=form, status=422 if form.errors else 200)
