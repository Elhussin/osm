from rest_framework import serializers
from apps.products.models import (
    ProductVariantReview, ProductVariantQuestion, ProductVariantAnswer, ProductVariantOffer
)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.products.serializers.product_support import (
    ProductVariantReviewSerializer, ProductVariantQuestionSerializer,
    ProductVariantAnswerSerializer, ProductVariantOfferSerializer
)
from core.views import BaseViewSet
class ProductVariantReviewViewSet(BaseViewSet):
    queryset = ProductVariantReview.objects.all()
    serializer_class = ProductVariantReviewSerializer
    permission_classes = [IsAuthenticated]

class ProductVariantQuestionViewSet(BaseViewSet):
    queryset = ProductVariantQuestion.objects.all()
    serializer_class = ProductVariantQuestionSerializer
    permission_classes = [IsAuthenticated]

class ProductVariantAnswerViewSet(BaseViewSet):
    queryset = ProductVariantAnswer.objects.all()
    serializer_class = ProductVariantAnswerSerializer
    permission_classes = [IsAuthenticated]

class ProductVariantOfferViewSet(BaseViewSet):
    queryset = ProductVariantOffer.objects.all()
    serializer_class = ProductVariantOfferSerializer
    permission_classes = [IsAuthenticated]

