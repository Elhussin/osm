# filters_utils.py
from typing import Type, Dict, Any, List
from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet
from django_filters import FilterSet

class FilterOptionsGenerator:
    """
    Generic class to generate filter options for a given queryset
    and optional filterset. Can be reused across different ViewSets.
    """
    def __init__(self, queryset: QuerySet, filterset_class: Type[FilterSet], query_params: Dict[str, Any] = None):
        self.queryset = queryset
        self.filterset_class = filterset_class
        self.query_params = query_params or {}

    def get_filtered_queryset(self) -> QuerySet:
        """
        Apply filters from query_params using the FilterSet.
        """
        if self.filterset_class:
            # Instantiate FilterSet with data + queryset
            filterset = self.filterset_class(data=self.query_params, queryset=self.queryset)
            if filterset.is_valid():
                return filterset.qs
        return self.queryset

    def generate_options(self, fields: List[str]) -> Dict[str, List[Any]]:
        """
        Generate distinct options for the given fields.
        Example: fields = ["customer__id", "customer__phone"]
        """
        filtered_qs = self.get_filtered_queryset()
        options = {}
        for field in fields:
            values = filtered_qs.values_list(field, flat=True).distinct()
            # Remove None values
            options[field] = list(filter(None, values))
        return options




def create_filterset_class(model: Type, fields: Dict[str, List[str]]) -> Type[FilterSet]:
    """
    Dynamically generate a FilterSet class for a given model and fields.
    
    Example usage:
        fields = {
            "customer__id": ["exact"],
            "customer__phone": ["icontains"],
        }
        MyFilterSet = create_filterset_class(PrescriptionRecord, fields)
    """
    # Note: Python does not allow referencing enclosing function variables directly
    # inside a class body (no closure lookup in class scope). To avoid NameError,
    # build the Meta and FilterSet classes dynamically with `type`.
    meta = type(
        "Meta",
        (),
        {
            "model": model,
            "fields": fields,
        },
    )

    filterset_name = f"{getattr(model, '__name__', 'Dynamic')}FilterSet"
    DynamicFilterSet = type(
        filterset_name,
        (FilterSet,),
        {
            "Meta": meta,
        },
    )

    return DynamicFilterSet


# 👇 دالة format تلقائي
def format_field_name(field: str) -> str:
    return field.replace("__", " ").replace("_", " ").title()


# 👇 دالة اختيار الاسم النهائي (custom label أو format)
def get_display_name(CUSTOM_FIELD_LABELS,field: str) -> str:
    return CUSTOM_FIELD_LABELS.get(field, format_field_name(field))
