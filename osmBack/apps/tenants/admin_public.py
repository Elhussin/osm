from django.contrib import admin
from apps.tenants.models import Client, Domain, PendingTenantRequest

admin.site.register(Client)
admin.site.register(Domain)
admin.site.register(PendingTenantRequest)
