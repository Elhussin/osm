# models.py - النماذج المحسنة
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from django.contrib.auth.models import User
from apps.branches.models import Branch,BranchUsers
from apps.crm.models import Customer
from core.models import BaseModel
from apps.products.models import Product, ProductVariant
from apps.prescriptions.models import PrescriptionRecord
from decimal import Decimal
import datetime
import uuid



class Stock(BaseModel):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE)
    variant = models.ForeignKey("ProductVariant", on_delete=models.CASCADE, related_name='stocks')
    # Stock quantities
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    max_stock_level = models.PositiveIntegerField(default=100)
    min_stock_level = models.PositiveIntegerField(default=0)
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Stock tracking
    last_restocked = models.DateTimeField(null=True, blank=True)
    last_sale = models.DateTimeField(null=True, blank=True)
    allow_backorder = models.BooleanField(default=False)

    class Meta:
        unique_together = [('branch', 'variant')]
        indexes = [
            models.Index(fields=['branch', 'quantity_in_stock']),
            models.Index(fields=['branch', 'is_active']),
        ]
    
    def __str__(self):  
        return f"{self.branch.name} - {self.variant} ({self.available_quantity} available)"

    @property
    def available_quantity(self):
        return max(0, self.quantity_in_stock - self.reserved_quantity)

    @property
    def stock_status(self):
        if self.available_quantity <= 0:
            return "Out of Stock"
        elif self.available_quantity <= self.reorder_level:
            return "Low Stock"
        elif self.quantity_in_stock > self.max_stock_level:
            return "Overstocked"
        return "In Stock"

    def reserve(self, quantity):
        if self.available_quantity >= quantity or self.allow_backorder:
            self.reserved_quantity = F('reserved_quantity') + quantity
            self.save(update_fields=['reserved_quantity'])
            return True
        return False

    def release_reserve(self, quantity):
        self.reserved_quantity = max(0, self.reserved_quantity - quantity)
        self.save(update_fields=['reserved_quantity'])
    
    def update_average_cost(self, new_quantity, new_cost):
        """تحديث التكلفة المتوسطة"""
        if self.quantity_in_stock > 0:
            total_cost = (self.quantity_in_stock * self.average_cost) + (new_quantity * new_cost)
            total_quantity = self.quantity_in_stock + new_quantity
            self.average_cost = total_cost / total_quantity if total_quantity > 0 else new_cost
        else:
            self.average_cost = new_cost
        self.last_cost = new_cost
    


class StockMovement(BaseModel):
    """Track all stock movements for audit purposes"""
    class MovementType(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase/Restock'
        SALE = 'sale', 'Sale'
        TRANSFER_IN = 'transfer_in', 'Transfer In'
        TRANSFER_OUT = 'transfer_out', 'Transfer Out'
        ADJUSTMENT = 'adjustment', 'Stock Adjustment'
        DAMAGE = 'damage', 'Damage/Loss'
        RETURN = 'return', 'Customer Return'
        RESERVE = 'reserve', 'Reserve Stock'
        RELEASE = 'release', 'Release Reserved'
    
    stock = models.ForeignKey("Stock", on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.IntegerField()
    quantity_before = models.PositiveIntegerField()
    quantity_after = models.PositiveIntegerField()
    reference_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    movement_date = models.DateTimeField(auto_now_add=True)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.stock} - {self.movement_type} ({self.quantity})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.movement_type == 'purchase' and self.cost_per_unit > 0 and hasattr(self, 'stock'):
            variant = self.stock.variant
            if variant:
                variant.last_purchase_price = self.cost_per_unit
                variant.save(update_fields=['last_purchase_price'])


class StockTransfer(BaseModel):
    """Stock transfers between branches"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUBMITTED = 'submitted', 'Submitted'
        SHIPPED = 'shipped', 'Shipped'
        RECEIVED = 'received', 'Received'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        
    
    from_branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name='outgoing_transfers')
    to_branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name='incoming_transfers')
    transfer_number = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_by = models.CharField(max_length=100, blank=True)
    approved_by = models.CharField(max_length=100, blank=True)

    # Dates
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            self.transfer_number = f"TRF-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transfer_number} | {self.from_branch.code} → {self.to_branch.code}"
    

    def execute_shipment(self):
        """ينفذ عملية الشحن (يخصم الكميات من الفرع المرسل)"""
        if self.status != 'submitted':
            raise ValueError("Only submitted transfers can be shipped.")

        with transaction.atomic():
            for item in self.items.select_for_update():
                # خصم من الفرع المرسل
                # Fixed: Use Stock instead of Inventory
                from_stock = Stock.objects.select_for_update().get(
                    branch=self.from_branch,
                    variant=item.variant
                )
                if from_stock.quantity_in_stock < item.quantity_requested:
                    raise ValueError(f"Insufficient stock for variant {item.variant}")

                from_stock.quantity_in_stock -= item.quantity_requested
                from_stock.save()

                item.quantity_sent = item.quantity_requested
                item.save()

                # سجل الحركة
                StockMovement.objects.create(
                    stock=from_stock,
                    movement_type='transfer_out',
                    quantity=-item.quantity_requested,
                    quantity_before=from_stock.quantity_in_stock + item.quantity_requested,
                    quantity_after=from_stock.quantity_in_stock,
                    notes=f"Transfer {self.transfer_number}"
                )

            self.status = 'shipped'
            self.shipped_date = timezone.now()
            self.save()

    def execute_receiving(self):
        """ينفذ عملية الاستلام (يضيف الكميات للفرع المستلم)"""
        if self.status != 'shipped':
            raise ValueError("Only shipped transfers can be received.")

        with transaction.atomic():
            for item in self.items.select_for_update():
                to_stock, _ = Stock.objects.select_for_update().get_or_create(
                    branch=self.to_branch,
                    variant=item.variant,
                    defaults={'quantity_in_stock': 0}
                )
                to_stock.quantity_in_stock += item.quantity_sent
                to_stock.save()

                item.quantity_received = item.quantity_sent
                item.save()

                StockMovement.objects.create(
                    stock=to_stock,
                    movement_type='transfer_in',
                    quantity=item.quantity_sent,
                    quantity_before=to_stock.quantity_in_stock - item.quantity_sent,
                    quantity_after=to_stock.quantity_in_stock,
                    notes=f"Transfer {self.transfer_number}"
                )

            self.status = 'received'
            self.received_date = timezone.now()
            self.save()


class StockTransferItem(BaseModel):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity_requested = models.PositiveIntegerField()
    quantity_sent = models.PositiveIntegerField(default=0)
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.variant} x {self.quantity_requested}"


