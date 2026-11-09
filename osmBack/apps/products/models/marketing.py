
from .product import ProductVariant
from core.models import BaseModel
from django.db import models

class ProductVariantMarketing(BaseModel):
    GENDER_CHOICES = [
        ('unisex', 'Unisex'),
        ('men', 'Men'),
        ('women', 'Women'),
        ('kids', 'Kids')
    ]

    AGE_GROUP_CHOICES = [
        ('adult', 'Adult'),
        ('child', 'Child'),
        ('senior', 'Senior')
    ]
    variant = models.ForeignKey(ProductVariant, related_name='marketing', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    seo_image = models.ImageField(upload_to='products/marketing/', blank=True, null=True)
    seo_image_alt = models.CharField(max_length=200, blank=True)

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, blank=True)
    
    def __str__(self):
        return f"{self.variant.product.name} - {self.variant.color}"


