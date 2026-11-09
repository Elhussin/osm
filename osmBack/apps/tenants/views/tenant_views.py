from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as T
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django_tenants.utils import  get_tenant
from core.views import BaseViewSet
from apps.tenants.models import (
    Client,
    SubscriptionPlan,
    PendingTenantRequest
)
from apps.tenants.serializers import (
    RegisterTenantSerializer,
    ClientSerializer,
    DomainSerializer,
        SubscriptionPlanSerializer
)
from core.utils.email import send_activation_email


class RegisterTenantView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        tenant = get_tenant(request)
        if tenant.schema_name != 'public':
            return HttpResponseForbidden("Not allowed on tenant domains.")
        
        serializer = RegisterTenantSerializer(data=request.data)
        if serializer.is_valid():
            pending = serializer.save()
            send_activation_email(pending.email, pending.token)
            return Response({"detail": T("Activation email sent.")}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==============================================================
# View Domain
# =============================================================
class DomainView(APIView):
    def get(self, request):
        tenant = get_tenant(request)
        if tenant.schema_name != 'public':
            return HttpResponseForbidden("Not allowed on tenant domains.")
        
        serializer = DomainSerializer(tenant)
        return Response(serializer.data)

# ==============================================================
# ClientViewSet
# ==============================================================

class ClientViewSet(BaseViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get the client associated with the user
        if self.request.user.role_id.name.lower() == 'owner' or self.request.user.is_superuser:
            return Client.objects.all()
            
        user_client = self.request.user.client
        if not user_client:
            return Client.objects.none()
        return Client.objects.filter(id=user_client.id)

    def retrieve(self, request, *args, **kwargs):
        # Check if the user has permission to view the client
        instance = self.get_object()
        if not request.user.client or instance.id != request.user.client.id:
            if self.request.user.role_id.name.lower() != 'owner':
                raise PermissionDenied("You do not have permission to view this client.")
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Check if the user has permission to create a client
        if not self.request.user.client:
            raise PermissionDenied("You do not have permission to create a client.")
        serializer.save(id=self.request.user.client.id)



class SubscriptionPlanViewSet(BaseViewSet):
    permission_classes = [AllowAny] 
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer

class RegisterTenantViewSet(BaseViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = PendingTenantRequest.objects.all()
    serializer_class = RegisterTenantSerializer
