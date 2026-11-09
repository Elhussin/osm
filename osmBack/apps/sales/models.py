# models.py بعد استخدام الخدمات (services) مع قاعدة BaseDocument و BaseItem

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from apps.crm.models import Customer
from apps.branches.models import Branch, BranchUsers
from core.models import BaseModel
from apps.products.models import ProductVariant
from apps.prescriptions.models import PrescriptionRecord
from decimal import Decimal
from apps.sales.services.order_service import confirm_order, cancel_order, calculate_order_totals
from apps.sales.services.invoice_service import confirm_invoice, calculate_invoice_totals
from apps.sales.services.payment_service import apply_payment

class BaseDocument(BaseModel):
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_branch')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='%(class)s_customer')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.15'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        abstract = True

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.total_amount


class BaseItem(BaseModel):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, related_name='%(class)s_variant')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Order(BaseDocument):
    ORDER_TYPE_choices = [ ('cash', 'cash'), ('credit', 'credit'), ('insurance', 'insurance') ]
    PAYMENT_TYPE_CHOICES = ORDER_TYPE_choices
    PAYMENT_STATUS_CHOICES = [ ('pending', 'Pending'), ('partial', 'Partial'), ('paid', 'Paid'), ('refunded', 'Refunded'), ('disputed', 'Disputed') ]
    STATUS_CHOICES = [ ('pending', 'pending'), ('confirmed', 'confirmed'), ('ready', 'ready'), ('delivered', 'delivered'), ('cancelled', 'cancelled') ]

    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_choices, default='cash')
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    expected_delivery = models.DateTimeField(null=True, blank=True)
    sales_person = models.ForeignKey(BranchUsers, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.customer.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            from apps.sales.utils import generate_serial_number
            self.order_number = generate_serial_number(Order, 'ORD', 'order_number')
        super().save(*args, **kwargs)

    def calculate_totals(self):
        return calculate_order_totals(self)

    def confirm(self, user):
        return confirm_order(self, user)

    def cancel(self, user):
        return cancel_order(self, user)


class OrderItem(BaseItem):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    prescription = models.ForeignKey(PrescriptionRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')

    def __str__(self):
        return f"{self.product_variant.product.model} - {self.quantity}"


class Invoice(BaseDocument):
    INVOICE_TYPES = [ ('purchase', 'Purchase'), ('sale', 'Sale'), ('return_purchase', 'Return Purchase'), ('return_sale', 'Return Sale') ]
    INVOICE_STATUS = [ ('draft', 'Draft'), ('paid', 'Paid'), ('partially_paid', 'Partially Paid'), ('overdue', 'Overdue'), ('confirmed', 'Confirmed') ]

    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES, default='sale')
    created_by = models.ForeignKey(BranchUsers, on_delete=models.SET_NULL, null=True, related_name='%(class)s_created_by')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_order')
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from apps.sales.utils import generate_serial_number
            self.invoice_number = generate_serial_number(Invoice, 'INV', 'invoice_number')
        super().save(*args, **kwargs)

    def calculate_totals(self):
        return calculate_invoice_totals(self)

    def confirm(self):
        return confirm_invoice(self)


class InvoiceItem(BaseItem):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')


class Payment(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='%(class)s_invoice')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[('cash', 'Cash'), ('card', 'Card')])

    def __str__(self):
        return f"Payment of {self.amount} for Invoice {self.invoice.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        apply_payment(self.invoice, self.amount)
