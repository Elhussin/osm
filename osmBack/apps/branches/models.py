from django.db import models
from core.models import BaseModel
from apps.hrm.models import Employee

# Create your models here.
class Branch(BaseModel):
    BRANCH_CHOICES = [
        ('store', 'Store'),
        ('branch', 'Branch'),
    ]
    name = models.CharField(max_length=100, unique=True)
    branch_code = models.CharField(max_length=10, unique=True, editable=False, blank=True)

    branch_type = models.CharField(max_length=10, choices=BRANCH_CHOICES)
    country = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    is_main_branch = models.BooleanField(default=False)
    allows_online_orders = models.BooleanField(default=True)

    operating_hours = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Branches"

    def save(self, *args, **kwargs):
        if not self.branch_code:
            prefix = "ST" if self.branch_type == "store" else "BR"
            # عدّ الفروع من نفس النوع للحصول على رقم متسلسل
            count = Branch.objects.filter(branch_type=self.branch_type).count() + 1
            code = f"{prefix}{count:03d}"

            # تأكد أنه غير مستخدم (في حالة حذف فرع قد يُعاد استخدام نفس الرقم)
            while Branch.objects.filter(branch_code=code).exists():
                count += 1
                code = f"{prefix}{count:03d}"

            self.branch_code = code

        super().save(*args, **kwargs)



class BranchUsers(BaseModel):

    branch_id = models.ForeignKey(Branch, on_delete=models.CASCADE)
    employee_id = models.ForeignKey(Employee, on_delete=models.CASCADE)
    status = models.BooleanField(default=True )     
    notes = models.TextField(null=True, blank=True)
    def __str__(self):
        return f"{self.employee.user.username} - {self.branch}"    
    
    class Meta:
        unique_together = ('branch_id', 'employee_id')

