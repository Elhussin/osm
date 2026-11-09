from rest_framework import serializers
from apps.products.models import Supplier, Manufacturer, Brand
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.products.serializers.suppliers import (
    SupplierSerializer, ManufacturerSerializer, BrandSerializer
)
from core.views import BaseViewSet

class SupplierViewSet(BaseViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

class ManufacturerViewSet(BaseViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer
    permission_classes = [IsAuthenticated]

class BrandViewSet(BaseViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated]

