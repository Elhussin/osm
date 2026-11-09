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
