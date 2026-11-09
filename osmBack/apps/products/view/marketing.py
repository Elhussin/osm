from apps.products.models import ProductVariantMarketing
from apps.products.serializers.marketing import ProductVariantMarketingSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.views import BaseViewSet
class ProductVariantMarketingViewSet(BaseViewSet):
    queryset = ProductVariantMarketing.objects.all()
    serializer_class = ProductVariantMarketingSerializer
    permission_classes = [IsAuthenticated]
