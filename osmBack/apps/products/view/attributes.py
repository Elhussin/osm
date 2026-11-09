from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.products.models import Attribute, AttributeValue
from apps.products.serializers.attributes import AttributeSerializer, AttributeValueSerializer
from core.views import BaseViewSet


ATTRIBUTES_RELATED_FIELDS = [
    "attribute_id__name",
]
ATTRIBUTES_FIELD_LABELS = {
    "attribute_id__name": "Attribute Name",
    "value": "Value",
}


ATTRIBUTES_FILTER_FIELDS = {
    "attribute_id__name": ["icontains"],
    "value": ["icontains"],
}

class AttributesViewSet(BaseViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer
    permission_classes = [IsAuthenticated]
    # search_fields = ['name']
    # filter_fields = ['name','is_active','is_deleted']
    # field_labels = {
    #     'name': 'Attribute Name',
    # }

class AttributeValueViewSet(BaseViewSet):
    queryset = AttributeValue.objects.all()
    serializer_class = AttributeValueSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ATTRIBUTES_RELATED_FIELDS
    field_labels = ATTRIBUTES_FIELD_LABELS
    filter_fields = ATTRIBUTES_FILTER_FIELDS
    # search_fields = ['value']
    # filter_fields = ['attribute_id__name','is_active','is_deleted']
    # field_labels = {
    #     'attribute_id__name': 'Attribute Name',
    #     'value': 'Attribute Value',
    #     'is_active': 'Is Active',
    # }
        

