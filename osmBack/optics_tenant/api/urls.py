# api/urls.py
from django.urls import path, include

urlpatterns = [

    path('core/', include('core.urls')),
    path('users/', include('apps.users.urls')),
    path('sales/', include('apps.sales.urls')),
    path('accounting/', include('apps.accounting.urls')),
    path('products/', include('apps.products.urls')),
    path('branches/', include('apps.branches.urls')),
    path('hrm/', include('apps.hrm.urls')),
    path('crm/', include('apps.crm.urls')),
    path('prescriptions/', include('apps.prescriptions.urls')),
    path('tenants/', include('apps.tenants.urls')),
]
