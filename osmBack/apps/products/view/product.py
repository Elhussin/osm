from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from rest_framework.request import Request
from apps.products.models import (
    Category, Product, ProductVariant, 
    ProductImage, FlexiblePrice,ProductVariantOffer
)


from apps.products.serializers import (
    ProductVariantSerializer, ProductSerializer, CategorySerializer,
 ProductImageSerializer, FlexiblePriceSerializer,ProductVariantOfferSerializer
)

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.views import BaseViewSet
class CategoryViewSet(BaseViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

# class LensCoatingViewSet(BaseViewSet):
#     queryset = LensCoating.objects.all()
#     serializer_class = LensCoatingSerializer
#     permission_classes = [IsAuthenticated]


class ProductVariantViewSet(BaseViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]

# class ProductVariantViewSet(viewsets.ModelViewSet):
#     queryset = ProductVariant.objects.all()

#     def get_serializer_class(self):
#         variant = self.get_object() if self.action in ['retrieve', 'update', 'partial_update'] else None
#         if variant:
#             return get_variant_serializer_class(variant.product_id.type)
        
#         # في حالة create، نقرأ نوع المنتج من البيانات القادمة
#         product_type = self.request.data.get('product_type')
#         return get_variant_serializer_class(product_type)


class ProductViewSet(BaseViewSet):

    queryset = (
        Product.objects.all()
        .select_related(
            'manufacturer_id',
            'category_id',
            'supplier_id',
            'brand_id'
        )  # للعلاقات ForeignKey
        .prefetch_related('variants')  # للعلاقات العكسية (OneToMany)
    )
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

class ProductImageViewSet(BaseViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]

class FlexiblePriceViewSet(BaseViewSet):
    queryset = FlexiblePrice.objects.all()
    serializer_class = FlexiblePriceSerializer
    permission_classes = [IsAuthenticated]

class ProductVariantOfferViewSet(BaseViewSet):
    queryset = ProductVariantOffer.objects.all()
    serializer_class = ProductVariantOfferSerializer
    permission_classes = [IsAuthenticated]
