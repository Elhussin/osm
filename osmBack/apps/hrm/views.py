from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework import viewsets
from .serializers import EmployeeSerializer, LeaveSerializer,AttendanceSerializer,PerformanceReviewSerializer,PayrollSerializer,TaskSerializer,NotificationSerializer,DepartmentSerializer
from .models import Employee,Leave,Attendance,PerformanceReview,Payroll,Task,Notification,Department
from django_filters.rest_framework import DjangoFilterBackend
from .filters import EmployeeFilter,DepartmentFilter
from core.utils.options_builder import build_choices_from_queryset, build_choices_from_list
from django.contrib.auth import get_user_model
from rest_framework import status
from core.views import BaseViewSet

User = get_user_model()


# class DepartmentViewSet(BaseViewSet):
#     queryset = Department.objects.all()
#     serializer_class = DepartmentSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = DepartmentFilter

#     def destroy(self, request, *args, **kwargs):
#         return Response({"detail": "You can't remove this item. Use  delete instead."}, status=405)

class DepartmentViewSet(BaseViewSet):

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DepartmentFilter

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Department.objects.all_objects()
        return Department.objects.all()
#     def destroy(self, request, *args, **kwargs):
#         return Response({"detail": "You can't remove this item. Use  delete instead."}, status=405)


class EmployeeFormOptionsView(APIView):
    def get(self, request):
        return Response({
            "departments": build_choices_from_queryset(Department.objects.all()),
            "users": build_choices_from_queryset(User.objects.all(), label_field="username"),
            "positions": build_choices_from_list(Employee.Position),
        })
        

class EmployeeViewSet(BaseViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeFilter


class LeaveViewSet(BaseViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer


class AttendanceViewSet(BaseViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


class PerformanceReviewViewSet(BaseViewSet):
    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer


class PayrollViewSet(BaseViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer


class TaskViewSet(BaseViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class NotificationViewSet(BaseViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
