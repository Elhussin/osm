from django.db import transaction
from apps.users.models import Branch
from apps.products.models import InventoryDocument, InventoryLineItem, StockMovement, Stock

@transaction.atomic
def create_inventory_document(document_type, branch, user, items, reference_number=None, notes=""):
    """
    items: list of dicts, each dict :
        - variant (ProductVariant)
        - quantity (int)
        - from_branch (Branch) (optional)
        - to_branch (Branch) (optional)
    """
    doc = InventoryDocument.objects.create(
        document_type=document_type,
        branch=branch,
        created_by=user,
        reference_number=reference_number or "",
        notes=notes
    )

    for item in items:
        variant = item['variant']
        quantity = item['quantity']
        from_branch = item.get('from_branch')
        to_branch = item.get('to_branch')

        InventoryLineItem.objects.create(
            document=doc,
            variant=variant,
            quantity=quantity,
            from_branch=from_branch,
            to_branch=to_branch
        )

        # تحديث الحركات وتعديل الكميات
        if document_type == 'transfer':
            process_stock_movement(variant, from_branch, quantity, 'transfer_out', user, reference_number=doc.id)
            process_stock_movement(variant, to_branch, quantity, 'transfer_in', user, reference_number=doc.id)
        elif document_type == 'purchase':
            process_stock_movement(variant, branch, quantity, 'in', user, reference_number=doc.id)
        elif document_type == 'sale':
            process_stock_movement(variant, branch, quantity, 'out', user, reference_number=doc.id)
        elif document_type == 'adjustment':
            process_stock_movement(variant, branch, quantity, 'adjustment', user, reference_number=doc.id)
        elif document_type == 'return':
            process_stock_movement(variant, branch, quantity, 'return', user, reference_number=doc.id)
        elif document_type == 'damage':
            process_stock_movement(variant, branch, quantity, 'damage', user, reference_number=doc.id)

    return doc


def process_stock_movement(variant, branch, quantity, movement_type, user, reference_number=None):
    if not branch or quantity == 0:
        return

    stock, created = Stock.objects.get_or_create(branch=branch, variant=variant)
    
    if movement_type in ['in', 'transfer_in', 'return']:
        stock.stock_quantity += quantity
    elif movement_type in ['out', 'transfer_out', 'damage']:
        stock.stock_quantity -= quantity
    elif movement_type == 'adjustment':
        # إذا كنت تريد التعديل المباشر للمخزون (موجب أو سالب)
        stock.stock_quantity += quantity

    stock.save()

    StockMovement.objects.create(
        branch=branch,
        variant=variant,
        movement_type=movement_type,
        quantity=quantity,
        reference_number=str(reference_number) if reference_number else '',
        created_by=user
    )

