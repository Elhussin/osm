
from paypalrestsdk.openid_connect import client_id
from rest_framework import serializers
from apps.tenants.models import Client, PendingTenantRequest, Payment,Domain,SubscriptionPlan
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from core.utils.ReusableFields import ReusableFields
from core.utils.check_unique_field import check_unique_field
from core.utils.expiration_date import expiration_date
from core.constants.tenants import PAYMENT_METHODS,PAYMENT_PERIODS
from core.mixins.VerboseNameMixin import VerboseNameMixin
import uuid
from django.contrib.auth.hashers import make_password

class SubscriptionPlanSerializer(VerboseNameMixin, serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'duration_months', 'duration_years', 'max_users',
            'max_branches', 'max_products', 'month_price', 'year_price', 'currency', 'discount','field_labels']


class RegisterTenantSerializer(serializers.ModelSerializer):
    email = ReusableFields.email()
    password = ReusableFields.password()
    name = ReusableFields.name()

    class Meta:
        model = PendingTenantRequest
        fields = ['name', 'email', 'password']

    def validate_email(self, value):
        return check_unique_field(PendingTenantRequest, 'email', value, self.instance)
    
    def validate_name(self, value):
        return check_unique_field(PendingTenantRequest, 'name', value, self.instance)

    def create(self, validated_data):


        name = validated_data['name']
        email = validated_data['email']
        password = validated_data['password']

        # Generate unique schema_name
        schema_base = slugify(name)
        schema_name = schema_base
        i = 1
        while Client.objects.filter(schema_name=schema_name).exists() or \
              PendingTenantRequest.objects.filter(schema_name=schema_name).exists():
            schema_name = f"{schema_base}{i}"
            i += 1

        # Apply trial limits
        trial_plan = SubscriptionPlan.objects.filter(name__iexact="trial").first()
        expires_at =expiration_date(days=trial_plan.duration_months)

        return PendingTenantRequest.objects.create(
            schema_name=schema_name,
            name=name,
            email=email,
            password=make_password(password),
            plan=trial_plan,
            expires_at=expires_at,
            token=uuid.uuid4(),
            token_expires_at=expiration_date(1)
        )




class ClientSerializer(VerboseNameMixin, serializers.ModelSerializer):
    plans = SubscriptionPlanSerializer(source='plan', read_only=True)  # <-- هنا التعديل
    is_paid = serializers.ReadOnlyField()
    is_plan_expired = serializers.ReadOnlyField()

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'max_users', 'max_products', 'max_branches',
            'paid_until', 'on_trial', 'is_active', 'is_deleted',
            'uuid', 'created_at', 'plans', 'is_paid', 'is_plan_expired', 'field_labels'
        ]
        read_only_fields = ['uuid', 'created_at', 'plans']

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = '__all__'


class CreatePaymentOrderSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()

    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.filter(is_active=True)
    )
    direction = serializers.ChoiceField(choices=PAYMENT_PERIODS)  # month / year
    method = serializers.ChoiceField(choices=PAYMENT_METHODS)

    def validate(self, data):
        # التحقق من العميل
        try:
            client = Client.objects.get(uuid=data["client_id"])
        except Client.DoesNotExist:
            raise serializers.ValidationError({"client_id": _("Client not found")})

        if not client.is_active:
            raise serializers.ValidationError({"client_id": _("Client account is inactive")})

        # التحقق من الخطة
        plan = data["plan_id"]
        direction = data["direction"]

        # تحديد المدة والسعر
        if direction == "month":
            amount = plan.month_price
        elif direction == "year":
            amount = plan.year_price
        else:
            raise serializers.ValidationError({"direction": _("Invalid payment direction")})

        # منع وجود دفعة معلقة لنفس الخطة
        pending_payments = Payment.objects.filter(
            client=client,
            plan=plan,
            status='pending'
        )
        if pending_payments.exists():
            raise serializers.ValidationError(
                _("You already have a pending payment for this plan")
            )

        data["client"] = client
        data["plan"] = plan
        data["amount"] = amount
        data["direction"] = direction
        data["method"] = data["method"]

        return data
