from .models import Stock

def get_variant_stock_summary(variant):
    """Get stock summary across all branches for a variant"""
    if hasattr(variant, 'stocks'):
        inventories = variant.stocks.select_related('branch')
        
        summary = {
            'total_stock': 0,
            'total_available': 0,
            'total_reserved': 0,
            'branches': [],
            'low_stock_branches': [],
            'out_of_stock_branches': [],
        }
        
        for inventory in inventories:
            summary['total_stock'] += inventory.quantity_in_stock
            summary['total_available'] += inventory.available_quantity
            summary['total_reserved'] += inventory.reserved_quantity
            
            branch_data = {
                'branch': inventory.branch,
                'stock': inventory.quantity_in_stock,
                'available': inventory.available_quantity,
                'reserved': inventory.reserved_quantity,
                'status': inventory.stock_status,
            }
            summary['branches'].append(branch_data)
            
            if inventory.stock_status == "Low Stock":
                summary['low_stock_branches'].append(inventory.branch)
            
            if inventory.stock_status == "Out of Stock":
                summary['out_of_stock_branches'].append(inventory.branch)
        
        return summary
    
    return None


def find_nearest_branch_with_stock(variant, user_location=None, min_quantity=1):
    """Find nearest branch with stock (simplified version)"""
    # available_inventories = BranchInventory.objects.get_available_branches(
    #     variant, min_quantity
    # )
    
    # Assuming available_quantity is what we care about
    # Stock has property available_quantity, but we should query DB efficiently.
    # available_quantity = quantity_in_stock - reserved_quantity
    # DB query for this requires F expression or annotation.
    # For simplicity, filtering by quantity_in_stock first, then python filter if needed, 
    # or just use quantity_in_stock if reservation isn't critical for "finding branch".
    # Better: Filter where quantity_in_stock >= min_quantity + reserved_quantity?
    # Simple query:
    available_stocks = Stock.objects.filter(
        variant=variant, 
        quantity_in_stock__gte=min_quantity
    ).select_related('branch')

    # Filter strictly for available_quantity in python if dataset is small, or use annotation
    available_stocks = [s for s in available_stocks if s.available_quantity >= min_quantity]
    
    # If no user location provided, return any available branch
    if not user_location or not available_stocks:
        return available_stocks[0] if available_stocks else None
    
    # Here you would implement actual location-based logic
    # For now, return the first available branch
    return available_stocks[0]


def can_fulfill_order_across_branches(items_dict):
    """
    Check if order can be fulfilled across branches
    items_dict: {variant: quantity, ...}
    """
    fulfillment_plan = {}
    
    for variant, needed_quantity in items_dict.items():
        # available_inventories = BranchInventory.objects.get_available_branches(variant)
        available_stocks = Stock.objects.filter(variant=variant).select_related('branch')
        # Sort by available quantity desc to minimize splits? Or by branch priority?
        # Let's sort by largest available first
        available_stocks = sorted(available_stocks, key=lambda s: s.available_quantity, reverse=True)
        
        remaining_quantity = needed_quantity
        variant_plan = []
        
        for inventory in available_stocks:
            if remaining_quantity <= 0:
                break
                
            available = inventory.available_quantity
            if available > 0:
                take_quantity = min(remaining_quantity, available)
                variant_plan.append({
                    'branch': inventory.branch,
                    'quantity': take_quantity,
                    'inventory': inventory
                })
                remaining_quantity -= take_quantity
        
        if remaining_quantity > 0:
            # Cannot fulfill this item completely
            return None
        
        fulfillment_plan[variant] = variant_plan
    
    return fulfillment_plan
