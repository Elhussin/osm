from django.contrib import admin

from .models import( Attribute, AttributeValue, ProductVariantMarketing
,ProductVariantReview, ProductVariantQuestion, ProductVariantAnswer, ProductVariantOffer
,Category, Product, ProductVariant ,ProductImage,FlexiblePrice,
    ExtraVariantAttribute,
    ContactLensVariant,
    ContactLensVariantExpirationDate,
    FrameVariant,
    StokLensVariant,
    RxLensVariant,
 Supplier, Manufacturer, Brand,
 Stock,StockMovement,StockTransfer, StockTransferItem
)

admin.site.site_header = "Optics Admin"
admin.site.site_title = "Optics Admin Portal"
admin.site.index_title = "Welcome to the Optics Admin Portal"

class ProductAdmin(admin.ModelAdmin):
    list_display = ('description',  'brand', 'created_at')
    search_fields = ('name',  'brand__name')
    list_filter = ('brand','type')
    ordering = ('-created_at',)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
class ProductVariantAdmin(admin.ModelAdmin):
    # list_display = ('product', 'variant_name','created_at')
    search_fields = ('product__name', 'variant_name')
    list_filter = ('product',)
    ordering = ('-created_at',)
    

admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
# admin.site.register(LensCoating)
admin.site.register(StockMovement)
admin.site.register(Stock)
admin.site.register(StockTransfer)
admin.site.register(StockTransferItem)
admin.site.register(ProductVariantMarketing)
admin.site.register(Attribute)
admin.site.register(AttributeValue)
admin.site.register(Supplier)
admin.site.register(Manufacturer)
admin.site.register(ProductImage)
admin.site.register(ProductVariantReview)
admin.site.register(ProductVariantQuestion)
admin.site.register(ProductVariantAnswer)
admin.site.register(ProductVariantOffer)
admin.site.register(FlexiblePrice)
admin.site.register(FrameVariant)
admin.site.register(StokLensVariant)
admin.site.register(RxLensVariant)
admin.site.register(ContactLensVariant)
admin.site.register(ContactLensVariantExpirationDate)
admin.site.register(ExtraVariantAttribute)

