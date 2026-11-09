
from rest_framework import viewsets
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .filters import CustomerFilter
from rest_framework.permissions import AllowAny
from .models import (
    Customer, CustomerGroup, Opportunity, Interaction, 
    Complaint, Subscription, Task,Campaign,Document,Contact
)
from .serializers import (
    CustomerSerializer, CustomerGroupSerializer, OpportunitySerializer, InteractionSerializer, 
    ComplaintSerializer, SubscriptionSerializer, TaskSerializer,CampaignSerializer,DocumentSerializer,ContactSerializer
)
from core.views import BaseViewSet


class CustomerViewSet(BaseViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CustomerFilter
 
    def get_queryset(self):
        return Customer.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        

class CustomerGroupViewSet(BaseViewSet):
    queryset = CustomerGroup.objects.all()
    serializer_class = CustomerGroupSerializer

    # def get_permissions(self):
    #     return get_default_permissions()

# OpportunityViewSet: get all ``Opportunity`` objects

class OpportunityViewSet(BaseViewSet):
    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer

    # def get_permissions(self):
    #     return super().get_default_permissions()
    
# InteractionViewSet: get all ``Interaction`` objects

class InteractionViewSet(BaseViewSet):
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    # def get_permissions(self):
    #     return super().get_default_permissions()
    
# ComplaintViewSet: get all ``Complaint`` objects

class ComplaintViewSet(BaseViewSet):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

    # def get_permissions(self):
    #     return super().get_default_permissions()
    
# SubscriptionViewSet: get all ``Subscription`` objects

class SubscriptionViewSet(BaseViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    # def get_permissions(self):
    #     return super().get_default_permissions()
    
# TaskViewSet: get all ``Task`` objects

class TaskViewSet(BaseViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    # def get_permissions(self):
    #     return super().get_default_permissions()
    
# CampaignViewSet: get all ``Campaign`` objects

class CampaignViewSet(BaseViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer

    # def get_permissions(self):
    #     return super().get_default_permissions()
    
# DocumentViewSet: get all ``Document`` objects

class DocumentViewSet(BaseViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    # def get_permissions(self):
    #     return super().get_default_permissions()
    
class ContactViewSet(BaseViewSet):
    permission_classes = [AllowAny]
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    
