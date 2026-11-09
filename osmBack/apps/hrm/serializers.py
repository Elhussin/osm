from rest_framework import serializers
from .models import (Department,Employee,Leave,Attendance,PerformanceReview,Payroll,Task,Notification)

class DepartmentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Department
        fields = '__all__'

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     data['is_active'] = instance.is_active
    #     data['is_deleted'] = instance.is_deleted
    #     return data

class EmployeeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user_id.username", read_only=True, default=None)
    department_name = serializers.CharField(source="department_id.name", read_only=True, default=None)

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     if instance.user is None:
    #         data["user_name"] = None
    #     if instance.department is None:
    #         data["department_name"] = None
    #     return data
    class Meta:
        model = Employee
        fields = [
            "id",
            "user_id",
            "department_id",
            "user_name",
            "department_name",
            "position",
            "salary",
            "phone",
            "hire_date",
            "is_active",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
    

class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

class PerformanceReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceReview
        fields = '__all__'

class PayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payroll
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
