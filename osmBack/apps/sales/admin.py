from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Order, OrderItem,Invoice,InvoiceItem,Payment
# Register your models here.


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'created_at', 'status')
    search_fields = ('order_number','customer__first_name','customer__last_name')
    list_filter = ('status', 'created_at')


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_variant', 'quantity', 'unit_price')
    search_fields = ('order__order_number', 'product_variant__product__model')
    list_filter = ('order__status', 'created_at')


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'created_at', 'status')
    search_fields = ('invoice_number', 'customer__first_name','customer__last_name')
    list_filter = ('status', 'created_at')


class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product_variant', 'quantity', 'unit_price')
    search_fields = ('invoice__invoice_number', 'product_variant__product__model')
    list_filter = ('invoice__status', 'created_at')


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_method', 'created_at')
    search_fields = ('invoice__invoice_number','invoice__customer__first_name','invoice__customer__last_name')
    list_filter = ('payment_method', 'created_at')
    @admin.display(description='Total Amount')
    def total_amount(self, obj):
        return obj.amount
    
    @admin.display(description='Payment Method')
    def payment_method(self, obj):
        return obj.payment_method
    

admin.site.register(Order,OrderAdmin)
admin.site.register(OrderItem,OrderItemAdmin)
admin.site.register(Invoice,InvoiceAdmin)
admin.site.register(InvoiceItem,InvoiceItemAdmin)
admin.site.register(Payment,PaymentAdmin)

