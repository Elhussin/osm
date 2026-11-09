from django.contrib import admin
from .models import Department, Employee,Leave,Attendance,PerformanceReview,Payroll,Task,Notification
# Register your models here.
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'position', 'phone', 'hire_date', 'is_active')
    search_fields = ('user__username', 'position')
    list_filter = ('position', 'is_active')
    ordering = ('-created_at',)

admin.site.register(Department)
admin.site.register(Employee,EmployeeAdmin)

admin.site.register(Leave)
admin.site.register(Attendance)
admin.site.register(PerformanceReview)
admin.site.register(Payroll)
admin.site.register(Task)
admin.site.register(Notification)
