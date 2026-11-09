from django.contrib import admin
from .models import Branch,BranchUsers
# Register your models here.
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch_code', 'branch_type', 'country', 'city', 'address', 'phone', 'email', 'operating_hours')
    search_fields = ('name', 'branch_code', 'branch_type', 'country', 'city', 'address', 'phone', 'email', 'operating_hours')
    list_filter = ('branch_type', 'country', 'city')
    ordering = ('-created_at',)


class BranchUsersAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'branch_id')
    search_fields = ('employee_id__name', 'branch_id__name')
    list_filter = ('branch_id',)
    ordering = ('-created_at',)

admin.site.register(Branch,BranchAdmin)
admin.site.register(BranchUsers,BranchUsersAdmin)
