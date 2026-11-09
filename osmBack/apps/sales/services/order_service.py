# services/order_service.py
from django.core.exceptions import ValidationError
from django.db import transaction
from apps.products.models import Stock, StockMovement
from apps.sales.services.base_document_service import calculate_document_totals

def calculate_order_totals(order):
    return calculate_document_totals(order)

@transaction.atomic
def confirm_order(order, user):
    if order.status != 'pending':
        raise ValidationError("Only pending orders can be confirmed")

    for item in order.items.select_related('variant'):
        stock = Stock.objects.select_for_update().filter(
            branch=order.branch,
            variant=item.variant
        ).first()

        if not stock or stock.available_quantity < item.quantity:
            raise ValidationError(f"Insufficient stock for {item.variant}")

        StockMovement.objects.create(
            stock=stock,
            movement_type='reserve',
            quantity=item.quantity,
            quantity_before=stock.quantity_in_stock,
            quantity_after=stock.quantity_in_stock - item.quantity,
            reference_number=order.order_number,
            notes=f"Reserved for order {order.order_number}",
        )
        stock.reserved_quantity += item.quantity
        stock.save()

    order.status = 'confirmed'
    order.confirmed_at = timezone.now()
    order.save(update_fields=['status', 'confirmed_at'])

@transaction.atomic
def cancel_order(order, user):
    if order.status not in ['pending', 'confirmed']:
        raise ValidationError("Cannot cancel this order")

    for item in order.items.select_related('variant'):
        stock = Stock.objects.select_for_update().filter(
            branch=order.branch,
            variant=item.variant
        ).first()
        if stock:
            StockMovement.objects.create(
                stock=stock,
                movement_type='release',
                quantity=item.quantity,
                quantity_before=stock.quantity_in_stock,
                quantity_after=stock.quantity_in_stock,
                reference_number=order.order_number,
                notes=f"Released from cancelled order {order.order_number}",
            )
            stock.reserved_quantity = max(0, stock.reserved_quantity - item.quantity)
            stock.save()

    order.status = 'cancelled'
    order.save(update_fields=['status'])

