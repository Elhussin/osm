# signals.py - إشارات النظام للتحديث التلقائي
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Order, OrderItem, Invoice, InvoiceItem, StockMovement, Stock


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_totals(sender, instance, **kwargs):
    """تحديث مجاميع الطلب عند تغيير العناصر"""
    if hasattr(instance, 'order') and instance.order:
        instance.order.calculate_totals()


@receiver(post_save, sender=InvoiceItem)
@receiver(post_delete, sender=InvoiceItem)
def update_invoice_totals(sender, instance, **kwargs):
    """تحديث مجاميع الفاتورة عند تغيير العناصر"""
    if hasattr(instance, 'invoice') and instance.invoice:
        instance.invoice.calculate_totals()


@receiver(post_save, sender=Order)
def check_order_status_change(sender, instance, created, **kwargs):
    """فحص تغيير حالة الطلب"""
    if not created and instance.status == 'delivered':
        # إنشاء فاتورة تلقائياً عند التسليم
        if not instance.invoices.exists():
            create_invoice_from_order(instance)


@receiver(post_save, sender=StockMovement)
def check_stock_levels(sender, instance, created, **kwargs):
    """فحص مستويات المخزون بعد كل حركة"""
    if created:
        stock = Stock.objects.filter(
            branch=instance.branch,
            variant=instance.variant
        ).first()
        
        if stock and stock.needs_reorder:
            # إرسال إشعار للمخزون المنخفض
            send_low_stock_notification(stock)


def create_invoice_from_order(order):
    """إنشاء فاتورة من الطلب"""
    with transaction.atomic():
        invoice = Invoice.objects.create(
            customer=order.customer,
            branch=order.branch,
            order=order,
            subtotal=order.subtotal,
            tax_rate=order.tax_rate,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            notes=f"Auto-generated from order {order.order_number}",
        )
        
        # نسخ عناصر الطلب إلى الفاتورة
        for order_item in order.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                variant=order_item.variant,
                quantity=order_item.quantity,
                unit_price=order_item.unit_price,
            )
        
        return invoice

import logging
logger = logging.getLogger(__name__)

def send_low_stock_notification(stock):
    logger.warning(f"LOW STOCK: {stock.variant} at {stock.branch} — Available: {stock.available_quantity}")
    """إرسال إشعار للمخزون المنخفض"""
