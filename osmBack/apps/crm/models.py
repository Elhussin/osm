from django.db import models

from core.models import BaseModel
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.contrib.auth import get_user_model
User = get_user_model()



class Customer(BaseModel):
    CUSTOMER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('agent', 'Agent'),
        ('supplier', 'Supplier'),
    ]
    """عملاء المتجر"""
    # Personal Information
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="crm_customer")
    first_name = models.CharField(max_length=100,blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    identification_number = models.CharField(max_length=20, unique=True,validators=[MinLengthValidator(10), MaxLengthValidator(10)],help_text="Enter a valid identification number 10 digits.")
    email = models.EmailField( blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPE_CHOICES, default='individual')
    
    
    # Address
    address_line1 = models.CharField(max_length=200, blank=True)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Membership
    customer_since = models.DateTimeField(auto_now_add=True)
    is_vip = models.BooleanField(default=False,null=True, blank=True)
    loyalty_points = models.IntegerField(default=0 ,null=True, blank=True)
    
    # Marketing
    accepts_marketing = models.BooleanField(default=True)
    registration_number = models.CharField(max_length=50, null=True, blank=True)
    tax_number = models.CharField(max_length=50, null=True, blank=True)
    preferred_contact = models.CharField(max_length=10, choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS')
    ], default='email')
    
    website = models.URLField(null=True, blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Interaction(BaseModel):
    INTERACTION_TYPES = [
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="interactions")
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.interaction_type} with {self.customer.user.username}"

class Complaint(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="complaints")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('resolved', 'Resolved')], default='open')

    def __str__(self):
        return f"Complaint by {self.customer.user.username}"
    

class Opportunity(BaseModel):
    STAGES = [
        ('lead', 'Lead'),
        ('qualified', 'Qualified'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="opportunities")
    title = models.CharField(max_length=255)
    stage = models.CharField(max_length=20, choices=STAGES, default='lead')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.stage}"
    
class Task(BaseModel):
    PRIORITIES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
class Campaign(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    customers = models.ManyToManyField(Customer, related_name="campaigns", blank=True)
    def __str__(self):
        return self.name

class Document(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="documents", null=True, blank=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')

    def __str__(self):
        return self.title


class Subscription(BaseModel):
    SUBSCRIPTION_TYPES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="subscriptions")
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES, verbose_name="Subscription Type")  # نوع الاشتراك
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="Start Date")  # تاريخ بدء الاشتراك
    end_date = models.DateTimeField(verbose_name="End Date")  # تاريخ انتهاء الاشتراك

    def __str__(self):
        return f"{self.customer.user.username} - {self.subscription_type}"

    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"


class CustomerGroup(BaseModel):
    name = models.CharField(max_length=100)
    customers = models.ManyToManyField(Customer, related_name="groups")
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Customer Group"
        verbose_name_plural = "Customer Groups"


class Contact(BaseModel):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    message = models.TextField(max_length=500)



    
