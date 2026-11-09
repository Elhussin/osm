from django.db import models
from core.models import BaseModel
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date

User = get_user_model()


class Department(BaseModel):
    name = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self):
        return self.name

class Employee(BaseModel):
    Position = [
        ('manager', 'Manager'),
        ('employee', 'Employee'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
        ('accountant', 'Accountant'),
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('delivery', 'Delivery'),
        ('customer_service', 'Customer Service'),
    ]
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee")
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    position = models.CharField(max_length=100,choices=Position ,default='employee')
    salary = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    hire_date = models.DateField(default=date.today)

    phone = models.CharField(max_length=20,blank=True)
    def __str__(self):
        return self.user_id.username


class Leave(models.Model):
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('vacation', 'Vacation Leave'),
        ('personal', 'Personal Leave'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leaves")
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPES)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')

    def __str__(self):
        return f"{self.leave_type} for {self.employee.user.username}"
    


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField()
    hours_worked = models.FloatField(null=True, blank=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.check_in and self.check_out:
            # Convert time to datetime using the date field
            from datetime import datetime
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)
            
            # Calculate hours worked
            delta = check_out_dt - check_in_dt
            self.hours_worked = delta.total_seconds() / 3600
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.employee.user.username} - {self.date}"
    
class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payrolls")
    month = models.CharField(max_length=20)  # أو يمكنك استخدام DateField
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.net_salary = self.basic_salary + self.bonuses - self.deductions
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.user.username} - {self.month}"
    
class PerformanceReview(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="performance_reviews")
    review_date = models.DateField(auto_now_add=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # من 1 إلى 5
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.user.username} - {self.review_date}"
    
class Task(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')], default='pending')

    def __str__(self):
        return f"{self.title} - {self.employee.user.username}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
    ('leave', 'Leave Request'),
    ('task', 'Task Assignment'),
    ('payroll', 'Payroll Update'),
    ]
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField(blank=True, null=True ,default="Notification")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.employee.user.username}"
