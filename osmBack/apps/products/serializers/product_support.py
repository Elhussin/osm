from rest_framework import serializers
from apps.products.models import (
    ProductVariantReview, ProductVariantQuestion, ProductVariantAnswer, ProductVariantOffer
)


class ProductVariantReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantReview
        fields = '__all__'

class ProductVariantQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantQuestion
        fields = '__all__'

class ProductVariantAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantAnswer
        fields = '__all__'

class ProductVariantOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariantOffer
        fields = '__all__'

