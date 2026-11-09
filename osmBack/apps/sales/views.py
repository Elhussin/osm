# views.py - Order API with actions

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.sales.models import Order,Invoice,Payment
from apps.sales.serializers import OrderSerializer,InvoiceSerializer,PaymentSerializer
from apps.sales.services.order_service import confirm_order, cancel_order, calculate_order_totals
from rest_framework.decorators import api_view
# views.py - Invoice API with actions

from apps.sales.models import Invoice
from apps.sales.serializers import InvoiceSerializer
from apps.sales.services.invoice_service import confirm_invoice, calculate_invoice_totals
from core.views import BaseViewSet
class OrderViewSet(BaseViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        confirm_order(order, request.user)
        return Response({'status': 'order confirmed'}, status=200)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        cancel_order(order, request.user)
        return Response({'status': 'order cancelled'}, status=200)

    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        order = self.get_object()
        calculate_order_totals(order)
        return Response({'total': order.total_amount}, status=200)




class InvoiceViewSet(BaseViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        invoice = self.get_object()
        confirm_invoice(invoice)
        return Response({'status': 'invoice confirmed'}, status=200)

    @action(detail=True, methods=['post'])
    def calculate_totals(self, request, pk=None):
        invoice = self.get_object()
        calculate_invoice_totals(invoice)
        return Response({'total': invoice.total_amount}, status=200)




class PaymentViewSet(BaseViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer 
    permission_classes = [IsAuthenticated]

# views.py - API for returning choices




@api_view(['GET'])
def order_choices(request):
    return Response({
        'order_type': Order.ORDER_TYPE_choices,
        'payment_type': Order.PAYMENT_TYPE_CHOICES,
        'status': Order.STATUS_CHOICES,
        'payment_status': Order.PAYMENT_STATUS_CHOICES,
    })

@api_view(['GET'])
def invoice_choices(request):
    return Response({
        'invoice_type': Invoice.INVOICE_TYPES,
        'status': Invoice.INVOICE_STATUS,
    })



# from apps.sales.permissions import IsBranchManagerOrReadOnly

# class OrderViewSet(BaseViewSet):
#     ...
#     permission_classes = [IsAuthenticated, IsBranchManagerOrReadOnly]
