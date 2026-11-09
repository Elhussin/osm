from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.conf import settings
from django.utils.text import slugify
import django.utils.timezone as timezone
from core.models import BaseModel, SoftDeleteManager, SoftDeleteMixin

class Role(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(
        'Permission',
        through='RolePermission',
        related_name='roles'
    )

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ['name']

class Permission(BaseModel):
    code = models.CharField(max_length=100, unique=True)  # مثل create_prescription
    description = models.TextField(blank=True)

class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('role', 'permission')

class SoftDeleteUserManager(SoftDeleteMixin, UserManager):
    pass

class User(AbstractUser):
    role = models.ForeignKey("Role", on_delete=models.SET_NULL, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE, null=True, blank=True)

    objects = SoftDeleteUserManager()

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


    def save(self, *args, **kwargs):
        # لو تم وضع is_deleted=True لأول مرة
        if self.is_deleted and not self.deleted_at:
            self.deleted_at = timezone.now()

        # لو تم استعادة العنصر
        elif not self.is_deleted and self.deleted_at:
            self.deleted_at = None

        super().save(*args, **kwargs)


class ContactUs(BaseModel):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    message = models.TextField(max_length=500)

class TenantSettings(BaseModel):
    business_name = models.CharField(max_length=255 , default="Optics Tenant")
    description = models.TextField(blank=True, default="This is a default description for the tenant settings.")
    # Social Media
    facebook = models.URLField(blank=True, default='https://www.facebook.com')
    instagram = models.URLField(blank=True, default='https://www.instagram.com')
    whatsapp = models.CharField(max_length=20, blank=True, default='whatsapp')
    twitter = models.URLField(blank=True, default='https://www.twitter.com')
    tiktok = models.URLField(blank=True, default='https://www.tiktok.com')
    linkedin = models.URLField(blank=True, default='https://www.linkedin.com')

    # Contact Info
    phone = models.CharField(max_length=20, blank=True, default='123-456-7890')
    email = models.EmailField(blank=True, default='email@example.com')
    website = models.URLField(blank=True, default='https://www.example.com')


    # SEO Settings
    seo_title = models.CharField(max_length=255, blank=True, default='Default SEO Title')
    seo_description = models.TextField(blank=True, default='Default SEO Description')
    seo_keywords = models.CharField(max_length=255, blank=True, default='keyword1, keyword2')

    # UI Preferences
    # primary_color = models.CharField(max_length=7, blank=True, default='#0000FF')  # Default to blue
    # secondary_color = models.CharField(max_length=7, blank=True, default='#FFFFFF')  # Default to white
    # logo = models.ImageField(upload_to='logos/', null=True, blank=True, default='logo.png')
    
    # Other Settings
    # timezone = models.CharField(max_length=50, blank=True, default='UTC')
    # currency = models.CharField(max_length=10, blank=True, default='USD')
    # date_format = models.CharField(max_length=20, blank=True, default='YYYY-MM-DD')
    # time_format = models.CharField(max_length=20, blank=True, default='24')

    address = models.CharField(max_length=255, blank=True, default='123 Default St, Default City, Default Country')
    city = models.CharField(max_length=100, blank=True, default='Default City')
    state = models.CharField(max_length=100, blank=True, default='Default State')
    postal_code = models.CharField(max_length=20, blank=True, default='12345')
    country = models.CharField(max_length=100, blank=True, default='Default Country')

    # bankDetails
    bank_name = models.CharField(max_length=100, blank=True, default='Default Bank')
    account_number = models.CharField(max_length=100, blank=True, default='123456789')
    iban = models.CharField(max_length=100, blank=True, default='DE89370400440532013000')
    swift_code = models.CharField(max_length=100, blank=True, default='DEUTDEDBFRA')

    def __str__(self):
        return self.business_name if self.business_name else "Tenant Settings"

class Page(BaseModel):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ar', 'Arabic'),
    ]
    slug = models.SlugField(max_length=200, unique=True)   
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pages')
    default_language = models.CharField(
        max_length=2, 
        choices=LANGUAGE_CHOICES, 
        default='en'
    )
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = 'pages'
        ordering = ['-updated_at']

class PageContent(BaseModel):
    page = models.ForeignKey(
        Page, 
        related_name='translations',  # ✅ عدلتها من pagecontent
        on_delete=models.CASCADE
    )
    language = models.CharField(max_length=2, choices=Page.LANGUAGE_CHOICES)
    title = models.CharField(max_length=200)
    # slug = models.SlugField(max_length=200)
    content = models.TextField(blank=True)
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    meta_keywords = models.TextField(blank=True)
    
    class Meta:
        db_table = 'page_translations'
        unique_together = [
            ['page', 'language'],
        ]
