from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import FilterSet

class FilterOptionsAPIViewMixin:
    """
    Mixin to provide automatic filtering for any APIView.
    Generates FilterSet dynamically from serializer or filter_fields.
    Also provides `filter_options` endpoint.
    """
    queryset = None
    serializer_class = None
    filter_fields = {}
    search_fields = []
    field_labels = {}

    def get_queryset(self):
        if self.queryset is None:
            raise NotImplementedError("You must define 'queryset' or override 'get_queryset'")
        return self.queryset

    def get_filterset_class(self):
        """
        Return dynamically generated FilterSet.
        """
        return create_filterset_class(
            model=self.get_queryset().model,
            fields=getattr(self, "filter_fields", {}),
            serializer_class=getattr(self, "serializer_class", None)
        )

    def filter_queryset(self, request):
        """
        Apply filter to queryset using GET params.
        """
        FilterSetClass = self.get_filterset_class()
        return FilterSetClass(request.GET, queryset=self.get_queryset()).qs

    @action(detail=False, methods=["get"])
    def filter_options(self, request):
        """
        API endpoint to fetch available filtering options (for frontend)
        """
        generator = FilterOptionsGenerator(
            queryset=self.get_queryset(),
            filterset_class=self.get_filterset_class(),
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
