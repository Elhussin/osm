# filters/base.py
import django_filters
from django.db import models


class DynamicCharFilter(django_filters.CharFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'icontains')
        super().__init__(*args, **kwargs)


class BaseFilterSet(django_filters.FilterSet):
    """
    FilterSet قابلة لإعادة الاستخدام للفلاتر الأساسية من نوع CharField وغيرها.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, filter_ in self.filters.items():
            # إضافة خيارات ديناميكية إذا كان الحقل نوعه Choice أو Char
            if isinstance(filter_.field, django_filters.fields.ChoiceField):
                model = self._meta.model
                field = model._meta.get_field(field_name)
                if isinstance(field, models.CharField) or isinstance(field, models.TextField):
                    choices = model.objects.values_list(field_name, flat=True).distinct()
                    filter_.extra['choices'] = [(v, v) for v in choices if v]

