from rest_framework import serializers
from apps.branches.models import Branch, BranchUsers

class BranchSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class BranchUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchUsers
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
