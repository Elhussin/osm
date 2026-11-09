# api/urls.py
from django.urls import path, include
from .views import (
    RegisterTenantView,
    ActivateTenantView,
    CreatePaymentOrderView,  # <-- الاسم الجديد
    PayPalExecuteView,
    PayPalCancelView,
    PayPalWebhookView,
    ClientViewSet,
    DomainView,
    SubscriptionPlanViewSet,
    PaymentListView,
    RegisterTenantViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plans')
router.register(r'registers', RegisterTenantViewSet, basename='register-tenant')
urlpatterns = [
    path("", include(router.urls)),
    path('register/', RegisterTenantView.as_view()),
    path('activate/', ActivateTenantView.as_view()),
    path("domain/", DomainView.as_view(), name="domain"),
    # Create payment order
    path('create-payment-order/', CreatePaymentOrderView.as_view(), name="create-payment-order"),
    # PayPal specific
    path('paypal/execute/', PayPalExecuteView.as_view(), name="execute-paypal-order"),
    path('paypal/cancel/', PayPalCancelView.as_view(), name="paypal-cancel"),
    path('paypal/webhook/', PayPalWebhookView.as_view(), name="paypal-webhook"),
    path('payments/', PaymentListView.as_view(), name="payments-list"),
]
