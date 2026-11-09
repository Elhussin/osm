from django.db import transaction
from django.core.management import call_command
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import logging
from enum import Enum
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as T
from django_tenants.utils import schema_context
from django.conf import settings
from apps.tenants.models import (
    PendingTenantRequest,
    Client,
    Domain,
    SubscriptionPlan
)
from core.utils.email import send_activation_email, send_message_acount_activated,send_failed_activation_email
from core.utils.expiration_date import expiration_date
import threading
paymant_logger = logging.getLogger('paypal')
tenant_logger = logging.getLogger('tenant')

import traceback
from django.core.exceptions import ValidationError



class ActivationStatus(Enum):
    SUCCESS = "success"
    TOKEN_MISSING = "token_missing" 
    INVALID_TOKEN = "invalid_token"
    ALREADY_ACTIVATED = "already_activated"
    TOKEN_EXPIRED = "token_expired"
    CREATION_FAILED = "creation_failed"
    POST_SETUP_FAILED = "post_setup_failed"

class TenantActivation:
    """
    Improved algorithm with better error handling and separation of concerns
    """
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger('tenant')
    
    def validate_token(self, token):
        """
        Algorithm: Token validation with early returns
        Time Complexity: O(1)
        """
        if not token:
            return None, ActivationStatus.TOKEN_MISSING
        
        try:
            pending = PendingTenantRequest.objects.get(token=token)
        except PendingTenantRequest.DoesNotExist:
            return None, ActivationStatus.INVALID_TOKEN
        
        if pending.is_activated:
            return pending, ActivationStatus.ALREADY_ACTIVATED
            
        return pending, ActivationStatus.SUCCESS
    
    def handle_token_expiration(self, pending):
        """
        Algorithm: Token expiration handling with automatic renewal
        Time Complexity: O(1)
        """
        if pending.token_expires_at < timezone.now():
            pending.token_expires_at = expiration_date(1)
            pending.save()
            send_activation_email(pending.email, pending.token)
            return ActivationStatus.TOKEN_EXPIRED
        return ActivationStatus.SUCCESS
    
    


    def create_tenant_atomic(self, pending):
        """
        Safer tenant creation with pre-checks and better error reporting
        """

        try:
            # ✅ Pre-checks before transaction
            # -------------------------------

            # Check schema name validity
            schema_name = slugify(pending.schema_name)
            if not schema_name:
                raise ValidationError("Invalid schema name")

            if Client.objects.filter(schema_name=schema_name).exists():
                raise ValidationError(f"Schema '{schema_name}' already exists")

            # Check subscription plan
            try:
                trial_plan = SubscriptionPlan.objects.get(name__iexact="trial")
            except SubscriptionPlan.DoesNotExist:
                raise ValidationError("Trial subscription plan not found")

            # Prepare domain
            domain = f"{schema_name}.{settings.TENANT_BASE_DOMAIN}"
            if Domain.objects.filter(domain=domain).exists():
                raise ValidationError(f"Domain '{domain}' already exists")

            # ✅ Transaction block
            # --------------------
            with transaction.atomic():
                tenant = Client.objects.create(
                    schema_name=schema_name,
                    name=pending.name,
                    plan=trial_plan,
                    max_users=trial_plan.max_users,
                    max_products=trial_plan.max_products,
                    max_branches=trial_plan.max_branches,
                    paid_until=expiration_date(trial_plan.duration_months),
                    on_trial=True,
                )
                # print("Tenant created")

                Domain.objects.create(
                    domain=domain,
                    tenant=tenant,
                    is_primary=True
                )
                # print("Domain created")

                # Mark pending request as activated
                pending.is_activated = True
                pending.is_deleted = True
                pending.save()
                return tenant, domain, ActivationStatus.SUCCESS

        except Exception as e:
            error_msg = f"Tenant creation failed: {str(e)}"
            # print(error_msg)
            traceback.print_exc()
            self.logger.error(error_msg)
            return None, None, ActivationStatus.CREATION_FAILED


    def setup_user_permissions(self, pending, tenant):
        """
        Algorithm: User and permission setup outside main transaction
        Time Complexity: O(1)
        """
        try:
            with schema_context(pending.schema_name):
                from django.contrib.auth import get_user_model
                from apps.users.models import Role, Permission, RolePermission
                
                # Create owner role and permissions
                owner_role, _ = Role.objects.get_or_create(
                    name="owner", 
                    defaults={"description": "Owner role"}
                )
                all_permission, _ = Permission.objects.get_or_create(
                    code="__all__", 
                    defaults={"description": "All permissions"}
                )
                RolePermission.objects.get_or_create(
                    role_id=owner_role, 
                    permission_id=all_permission
                )
                
                # Create superuser
                User = get_user_model()
                User.objects.create_superuser(
                    username=pending.name,
                    email=pending.email,
                    password=pending.password,
                    role_id=owner_role,
                    client=tenant
                )
                call_command('import_csv_with_foreign', schema=pending.schema_name, config="data/csv_config.json")
                # call_command()
            return ActivationStatus.SUCCESS
            
        except Exception as e:
            self.logger.warning(f"Post-activation setup failed: {str(e)}")
            return ActivationStatus.POST_SETUP_FAILED





# OPTIMIZED VIEW IMPLEMENTATION
# =============================

class ActivateTenantView(APIView):
    permission_classes = [AllowAny]
    
    def __init__(self):
        super().__init__()
        self.tenantActivation = TenantActivation()
    
    def get(self, request):
        """
        Main algorithm execution with improved flow control
        """
        token = request.query_params.get("token")
        
        # Step 1: Validate token
        pending, status = self.tenantActivation.validate_token(token)
        if status != ActivationStatus.SUCCESS:
            return self._handle_validation_error(status, pending)
        
        # Step 2: Check token expiration
        expiration_status = self.tenantActivation.handle_token_expiration(pending)
        if expiration_status == ActivationStatus.TOKEN_EXPIRED:
            return Response({
                "detail": T("Activation link expired. New activation email sent.")
            }, status=400)
        
        ResponseData = {
            "detail": T("Start creating your store. Please wait You will receive a confirmation email. "),
            # "tenant_domain": domain,
        }

        
        threading.Thread(target=self._background_activation, args=(pending,)).start()

        return Response(ResponseData, status=200)


    def _background_activation(self, pending):

        tenant, domain, creation_status = self.tenantActivation.create_tenant_atomic(pending)
  
        if creation_status != ActivationStatus.SUCCESS:
            send_failed_activation_email(pending.email)
            return

        self.tenantActivation.setup_user_permissions(pending, tenant)

        send_message_acount_activated(pending.email, pending.schema_name, pending.name)


    def _handle_validation_error(self, status, pending):
        """Helper method for handling validation errors"""
        error_messages = {
            ActivationStatus.TOKEN_MISSING: T("Token is required."),
            ActivationStatus.INVALID_TOKEN: T("Invalid or expired activation link."),
            ActivationStatus.ALREADY_ACTIVATED: T("Your account is already activated. Please login."),
        }
        return Response({"detail": error_messages[status]}, status=400)


