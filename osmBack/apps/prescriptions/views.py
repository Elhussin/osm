from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from core.views import BaseViewSet
from .models import PrescriptionRecord
from .serializers import PrescriptionRecordSerializer
from core.utils.filters_utils import FilterOptionsGenerator,get_display_name
from core.utils.create_filterset import create_filterset_class
from core.permissions.RoleOrPermissionRequired import RoleOrPermissionRequired
CUSTOMER_RELATED_FIELDS = [
    "customer__id",
    "customer__phone",
    "customer__first_name",
    "customer__last_name",
    "created_by__username",
]
# # 👇 أسماء مخصصة لبعض الحقول
CUSTOMER_FIELD_LABELS = {
    "customer__first_name": "First Name",
    "customer__last_name": "Last Name",
    "created_by__username": "Created By",
    "customer__phone": "Phone",
    

}

# 👇 تعريف الحقول للفلترة الدقيقة
CUSTOMER_FILTER_FIELDS = {
    "customer__id": ["exact"],
    "customer__phone": ["icontains"],
    "customer__email": ["icontains"],
    "customer__first_name": ["icontains"],
    "customer__last_name": ["icontains"],
    "created_by__username": ["icontains"],
    "created_by__first_name": ["icontains"],
}


class PrescriptionViewSet(BaseViewSet):
    queryset = PrescriptionRecord.objects.select_related("customer", "created_by").all()
    serializer_class = PrescriptionRecordSerializer
    search_fields = CUSTOMER_RELATED_FIELDS
    field_labels = CUSTOMER_FIELD_LABELS
    filter_fields = CUSTOMER_FILTER_FIELDS

    permission_classes = [
        IsAuthenticated,
        RoleOrPermissionRequired(
            allowed_roles=["staff", "OWNER"],
            required_permissions=["view_prescriptions"]
        )
    ]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

# to use this view add this to urls
# class PrescriptionListAPIView(FilterOptionsAPIViewMixin, APIView):
#     queryset = PrescriptionRecord.objects.select_related("customer", "created_by").all()
#     serializer_class = PrescriptionRecordSerializer
#     filter_fields = CUSTOMER_FILTER_FIELDS
#     search_fields = CUSTOMER_RELATED_FIELDS
#     field_labels = CUSTOMER_FIELD_LABELS

#     def get(self, request):
#         # تطبيق الفلترة
#         filtered_qs = self.filter_queryset(request)
#         serializer = self.serializer_class(filtered_qs, many=True)
#         return Response(serializer.data)
