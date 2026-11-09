from django.contrib import admin
from .models import PrescriptionRecord
# Register your models here.
class PrescriptionRecordAdmin(admin.ModelAdmin):
    list_display = ('customer', 'prescription_date', 'right_sphere', 'right_cylinder', 'right_axis', 'left_sphere', 'left_cylinder', 'left_axis')
    list_filter = ('customer', 'prescription_date')
    search_fields = ('customer__full_name', 'customer__email')
admin.site.register(PrescriptionRecord)
