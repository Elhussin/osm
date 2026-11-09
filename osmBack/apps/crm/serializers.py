from rest_framework import serializers
from .models import (
    Customer, CustomerGroup, Opportunity, Interaction, 
    Complaint, Subscription, Task,Campaign,Document,Contact
)

from django.contrib.auth import get_user_model

from rest_framework import serializers

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'phone','identification_number',
           'first_name',
            'last_name', 'email', 
            'customer_type', 'is_vip',
            'accepts_marketing', 'registration_number',
            'tax_number', 'preferred_contact', 'website',
            'description',
             'address_line1', 'address_line2',
               'city', 'postal_code','is_active','is_deleted'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

        extra_kwargs = {
            'phone': {
                'error_messages': {
                    'required': 'Phone number is required.',
                    'blank': 'Please enter a valid phone number.'
                }
            },
            'email': {
                'error_messages': {
                    'required': 'Email is required.',
                    'blank': 'Please enter a valid email address.'
                }
            },
            'identification_number': {
                'error_messages': {
                    'required': 'Identification number is required.',
                    'blank': 'Please enter a valid identification number.'
                }
            },
            'customer_type': {
                'error_messages': {
                    'required': 'Customer type is required.',
                    'blank': 'Please select a valid customer type.'
                }
            },
            'phone': {
                'error_messages': {
                    'required': 'Phone number is required.',
                    'blank': 'Please enter a valid phone number.'
                }
            },
            'first_name': {
                'error_messages': {
                    'required': 'First name is required.',
                    'blank': 'Please enter a valid first name.'
                }
            },
            'last_name': {
                'error_messages': {
                    'required': 'Last name is required.',
                    'blank': 'Please enter a valid last name.'
                }
            },
        }

    def create(self, validated_data):
        # Add the current user to the new customer
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class OpportunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Opportunity
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class CustomerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerGroup
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
