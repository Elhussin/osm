
from django_filters import rest_framework as filters
from core.filters.base import BaseFilterSet, DynamicCharFilter  # إذا كنت تستخدمها
from .models import Employee,Department

class EmployeeFilter(BaseFilterSet):
    user__username = DynamicCharFilter(label="Username")
    phone = DynamicCharFilter()
    position = filters.MultipleChoiceFilter(choices=Employee.Position)
    department = filters.ModelChoiceFilter(queryset=Department.objects.all())
    salary_min = filters.NumberFilter(field_name="salary", lookup_expr="gte", label="Min Salary")
    salary_max = filters.NumberFilter(field_name="salary", lookup_expr="lte", label="Max Salary")
    hire_date = filters.DateFromToRangeFilter()  # ?hire_date_after=2024-01-01&hire_date_before=2025-01-01

    class Meta:
        model = Employee
        fields = [
            'user__username',
            'phone',
            'position',
            'department',
            'salary_min',
            'salary_max',
            'hire_date',
        ]


class DepartmentFilter(BaseFilterSet):
    name = DynamicCharFilter()
    description = DynamicCharFilter()
    location = DynamicCharFilter()
    
    class Meta:
        model = Department
        fields = [
            'name',
            'description',
            'location',
        ]
