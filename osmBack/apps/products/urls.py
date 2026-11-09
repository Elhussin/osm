

from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .view import (
AttributesViewSet, AttributeValueViewSet,
 ProductVariantMarketingViewSet
,ProductVariantReviewViewSet, ProductVariantQuestionViewSet, ProductVariantAnswerViewSet, ProductVariantOfferViewSet
,CategoryViewSet, ProductViewSet, ProductVariantViewSet, ProductImageViewSet,FlexiblePriceViewSet
,SupplierViewSet, ManufacturerViewSet, BrandViewSet
,StocksViewSet, StockMovementsViewSet, StockTransferViewSet, StockTransferItemViewSet
)

router = DefaultRouter()
router.register(r'variants', ProductVariantViewSet, basename='product-variant')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'manufacturers', ManufacturerViewSet, basename='manufacturer')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'attributes', AttributesViewSet, basename='attributes')
router.register(r'attribute-values', AttributeValueViewSet, basename='attribute-value')
router.register(r'marketing', ProductVariantMarketingViewSet, basename='product-variant-marketing')
router.register(r'reviews', ProductVariantReviewViewSet, basename='product-variant-review')
router.register(r'questions', ProductVariantQuestionViewSet, basename='product-variant-question')
router.register(r'answers', ProductVariantAnswerViewSet, basename='product-variant-answer')
router.register(r'offers', ProductVariantOfferViewSet, basename='product-variant-offer')
router.register(r'categories', CategoryViewSet, basename='category')
# router.register(r'lens-coatings', LensCoatingViewSet, basename='lens-coating')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'flexible-prices', FlexiblePriceViewSet, basename='flexible-price')
router.register(r'stocks', StocksViewSet, basename='stocks')
router.register(r'stock-movements', StockMovementsViewSet, basename='stock-movements')
router.register(r'stock-transfers', StockTransferViewSet, basename='stock-transfer')
router.register(r'stock-transfer-items', StockTransferItemViewSet, basename='stock-transfer-item')


urlpatterns = [
    path('', include(router.urls)),
]
