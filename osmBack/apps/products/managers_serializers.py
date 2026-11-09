# serializers.py
from rest_framework import serializers
from .models import Branch, BranchInventory

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class BranchInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchInventory
        fields = '__all__'
