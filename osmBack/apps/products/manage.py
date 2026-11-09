# ============ Manager Classes ============

class BranchQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    
    def main_branch(self):
        return self.filter(is_main_branch=True).first()
    
    def by_city(self, city):
        return self.filter(city__icontains=city)


class BranchManager(models.Manager):
    def get_queryset(self):
        return BranchQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def main_branch(self):
        return self.get_queryset().main_branch()


class BranchInventoryQuerySet(models.QuerySet):
    def for_branch(self, branch):
        return self.filter(branch=branch)
    
    def low_stock(self):
        return self.filter(quantity_in_stock__lte=models.F('reorder_level'))
    
    def out_of_stock(self):
        return self.filter(quantity_in_stock__lte=models.F('reserved_quantity'))
    
    def in_stock(self):
        return self.filter(quantity_in_stock__gt=models.F('reserved_quantity'))
    
    def by_variant_type(self, variant_model):
        """Filter by variant type (EyewearVariant, LensVariant, etc.)"""
        if variant_model == EyewearVariant:
            return self.filter(eyewear_variant__isnull=False)
        elif variant_model == LensVariant:
            return self.filter(lens_variant__isnull=False)
        elif variant_model == AccessoryVariant:
            return self.filter(accessory_variant__isnull=False)
        return self.none()


class BranchInventoryManager(models.Manager):
    def get_queryset(self):
        return BranchInventoryQuerySet(self.model, using=self._db)
    
    def for_branch(self, branch):
        return self.get_queryset().for_branch(branch)
    
    def low_stock(self):
        return self.get_queryset().low_stock()
    
    def get_total_stock(self, variant):
        """Get total stock across all branches for a variant"""
        if hasattr(variant, 'branch_inventories'):
            return variant.branch_inventories.aggregate(
                total=models.Sum('quantity_in_stock')
            )['total'] or 0
        return 0
    
    def get_available_branches(self, variant, min_quantity=1):
        """Get branches that have the variant in stock"""
        if hasattr(variant, 'branch_inventories'):
            return variant.branch_inventories.filter(
                quantity_in_stock__gte=min_quantity + models.F('reserved_quantity')
            ).select_related('branch')
        return self.none()


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)
    
    def by_type(self, product_type):
        return self.filter(type=product_type)
    
    def with_variants(self):
        return self.prefetch_related('variants')


class ProductManager(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def by_type(self, product_type):
        return self.get_queryset().by_type(product_type)


# Add managers to models
Product.add_to_class('objects', ProductManager())
Branch.add_to_class('objects', BranchManager())
BranchInventory.add_to_class('objects', BranchInventoryManager())


# ============ Helper Functions ============

def get_variant_stock_summary(variant):
    """Get stock summary across all branches for a variant"""
    if hasattr(variant, 'branch_inventories'):
        inventories = variant.branch_inventories.select_related('branch')
        
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
            
            if inventory.needs_reorder:
                summary['low_stock_branches'].append(inventory.branch)
            
            if inventory.is_out_of_stock:
                summary['out_of_stock_branches'].append(inventory.branch)
        
        return summary
    
    return None


def find_nearest_branch_with_stock(variant, user_location=None, min_quantity=1):
    """Find nearest branch with stock (simplified version)"""
    available_inventories = BranchInventory.objects.get_available_branches(
        variant, min_quantity
    )
    
    # If no user location provided, return any available branch
    if not user_location or not available_inventories.exists():
        return available_inventories.first()
    
    # Here you would implement actual location-based logic
    # For now, return the first available branch
    return available_inventories.first()


def can_fulfill_order_across_branches(items_dict):
    """
    Check if order can be fulfilled across branches
    items_dict: {variant: quantity, ...}
    """
    fulfillment_plan = {}
    
    for variant, needed_quantity in items_dict.items():
        available_inventories = BranchInventory.objects.get_available_branches(variant)
        
        remaining_quantity = needed_quantity
        variant_plan = []
        
        for inventory in available_inventories:
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
