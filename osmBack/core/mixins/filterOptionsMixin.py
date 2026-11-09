from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import FilterSet
from core.utils.filters_utils import FilterOptionsGenerator, get_display_name
from core.utils.create_filterset import create_filterset_class


class FilterOptionsMixin:
    """
    Mixin that dynamically generates filtering options for any ViewSet.
    """
    filter_fields = {}
    field_labels = {}
    search_fields = []

    def get_filterset_class(self):
        """
        Generate FilterSet dynamically if not explicitly set.
        """
        # إذا الكلاس عنده filterset_class جاهزة
        explicit_class = getattr(self, "__explicit_filterset_class", None)
        if explicit_class and issubclass(explicit_class, FilterSet):
            return explicit_class

        model = self.queryset.model
        return create_filterset_class(
            model=model,
            fields=getattr(self, "filter_fields", {}),
            serializer_class=getattr(self, "serializer_class", None),
        )

    @action(detail=False, methods=["get"])
    def filter_options(self, request):
        """
        API endpoint to fetch available filtering options (for frontend).
        """
        FilterSet = self.get_filterset_class()
        generator = FilterOptionsGenerator(
            queryset=self.get_queryset(),
            filterset_class=FilterSet,
            query_params=request.query_params,
        )
        options = generator.generate_options(getattr(self, "search_fields", []))

        formatted_options = [
            {
                "name": field,
                "label": get_display_name(getattr(self, "field_labels", {}), field),
                "values": values,
            }
            for field, values in options.items()
        ]
        return Response(formatted_options)
