# urls.py - routing OrderViewSet

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sales.views import OrderViewSet,InvoiceViewSet,PaymentViewSet,order_choices,invoice_choices

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('orders/choices/', order_choices, name='order-choices'),
    path('invoices/choices/', invoice_choices, name='invoice-choices'),
]

 
