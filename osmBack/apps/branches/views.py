from django.shortcuts import render
from rest_framework import viewsets
from .serializers import *
from .models import *
from core.views import BaseViewSet


class BranchViewSet(BaseViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer


class BranchUsersViewSet(BaseViewSet):
    queryset = BranchUsers.objects.all()
    serializer_class = BranchUsersSerializer




# Create your views here.
