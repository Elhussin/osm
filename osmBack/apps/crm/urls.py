from .views import *
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'customer-groups', CustomerGroupViewSet, basename='customer-group')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'interactions', InteractionViewSet, basename='interaction')
router.register(r'complaints', ComplaintViewSet, basename='complaint')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'contact-us', ContactViewSet, basename='contact-us')

urlpatterns = [
    path('', include(router.urls)),
]
