from typing import Dict, List, Type, Optional
from django_filters import FilterSet, CharFilter, NumberFilter, DateFilter, BooleanFilter
from django.db import models

def create_filterset_class(
    model: Type[models.Model],
    fields: Dict[str, List[str]],
    field_types: Optional[Dict[str, str]] = None,
    serializer_class=None,
) -> Type[FilterSet]:
    field_types = field_types or {}
    model_fields = {f.name: f for f in model._meta.get_fields() if hasattr(f, "get_internal_type")}

    def detect_filter_type(field_name: str) -> str:
        if field_name in field_types:
            return field_types[field_name]

        base_field = field_name.split("__")[0]
        field_obj = model_fields.get(base_field)
        if not field_obj:
            return "char"

        internal_type = field_obj.get_internal_type()
        if internal_type in ["IntegerField", "FloatField", "DecimalField"]:
            return "number"
        elif internal_type in ["DateField", "DateTimeField"]:
            return "date"
        elif internal_type in ["BooleanField", "NullBooleanField"]:
            return "boolean"
        return "char"

    allowed_fields = set(fields.keys())
    if serializer_class:
        serializer_fields = set(serializer_class().fields.keys())
        allowed_fields &= serializer_fields or allowed_fields

    filters = {}
    type_map = {
        "char": CharFilter,
        "number": NumberFilter,
        "date": DateFilter,
        "boolean": BooleanFilter,
    }

    for field_name, lookups in fields.items():
        if serializer_class and field_name not in allowed_fields:
            continue

        detected_type = detect_filter_type(field_name)
        base_class = type_map.get(detected_type, CharFilter)

        for lookup_expr in lookups:
            filter_key = f"{field_name}__{lookup_expr}" if lookup_expr != "exact" else field_name
            filters[filter_key] = base_class(field_name=field_name, lookup_expr=lookup_expr)

    # meta = type("Meta", (), {"model": model, "fields": fields})
    meta = type("Meta", (), {"model": model, "fields": list(fields.keys())})
    filterset_name = f"{getattr(model, '__name__', 'Dynamic')}FilterSet"

    return type(filterset_name, (FilterSet,), {**filters, "Meta": meta})
