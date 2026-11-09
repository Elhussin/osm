from core.models import BaseModel
from django.db import models



class Manufacturer(BaseModel):
    """Manufacturer for glasses"""
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"

class Brand(BaseModel):
    """Brand for glasses"""
    PRODUCT_TYPE_CHOICES = [
        ('CL', 'Contact Lenses'),
        ('SL', 'Spectacle Lenses'),
        ('FR', 'Frames'),
        ('AX', 'Accessories'),
        ('OT', 'Other'),
        ('DV', 'Devices'),
        ('All', 'All')
    ]

    name = models.TextField(max_length=100, unique=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPE_CHOICES , default='All')
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

class Supplier(BaseModel):
    """Suppliers"""
    name = models.TextField(max_length=50, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"


