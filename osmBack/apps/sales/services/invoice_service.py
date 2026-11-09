# services/invoice_service.py

from django.db import transaction
from django.core.exceptions import ValidationError
from apps.products.models import Stock, StockMovement
from apps.sales.services.base_document_service import calculate_document_totals


def calculate_invoice_totals(invoice):
    return calculate_document_totals(invoice)

@transaction.atomic
def confirm_invoice(invoice):
    if invoice.status != 'draft':
        raise ValidationError("Only draft invoices can be confirmed")

    for item in invoice.items.select_related('product_variant'):
        stock = Stock.objects.select_for_update().filter(
            branch=invoice.branch,
            variant=item.product_variant
        ).first()

        if invoice.invoice_type in ['sale', 'return_purchase']:
            if stock.available_quantity < item.quantity:
                raise ValidationError(f"Not enough stock for {item.product_variant}")
            stock.quantity_in_stock -= item.quantity
            movement_type = 'sale'
        else:
            stock.quantity_in_stock += item.quantity
            movement_type = 'purchase'

        before = stock.quantity_in_stock
        stock.save()

        StockMovement.objects.create(
            stock=stock,
            movement_type=movement_type,
            quantity=item.quantity if movement_type == 'purchase' else -item.quantity,
            quantity_before=before,
            quantity_after=stock.quantity_in_stock,
            reference_number=invoice.invoice_number,
            notes=f"Invoice {invoice.invoice_type}",
        )

    invoice.status = 'confirmed'
    invoice.save()
