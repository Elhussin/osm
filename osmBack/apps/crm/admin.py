from django.contrib import admin
from .models import Customer, Interaction, Complaint, Opportunity, Task, Campaign, Document, Subscription, CustomerGroup
# Register your models here.

admin.site.register(Customer)
admin.site.register(Interaction)    
admin.site.register(Complaint)
admin.site.register(Opportunity)
admin.site.register(Task)
admin.site.register(Campaign)
admin.site.register(Document)
admin.site.register(Subscription)
admin.site.register(CustomerGroup)
