from django.db import models
from .product import ProductVariant
from apps.crm.models import Customer
from core.models import BaseModel
from django.contrib.auth import get_user_model
User = get_user_model()

class ProductVariantReview(BaseModel):
    ProductVariant_id = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    review = models.TextField()
    reviewed_by = models.ForeignKey(Customer, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Review for {self.ProductVariant.product.model} by {self.reviewed_by.user.username}"
    
class ProductVariantQuestion(BaseModel):
    ProductVariant_id = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    asked_by = models.ForeignKey(Customer, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Question about {self.ProductVariant.product.model} by {self.asked_by.user.username}"
    
class ProductVariantAnswer(BaseModel):
    question_id = models.OneToOneField(ProductVariantQuestion, on_delete=models.CASCADE, related_name='answer')
    answer = models.TextField()
    answered_by = models.ForeignKey(User, on_delete=models.CASCADE)
    def __str__(self):
        return f"Answer for {self.question.ProductVariant.product.model} question by {self.answered_by.user.username}"

class ProductVariantOffer(BaseModel):
    ProductVariant_id = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='offers')
    offer = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"{self.offer} on {self.ProductVariant.product.model}"


