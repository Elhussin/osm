
from apps.products.models import Stock, StockMovement, StockTransfer, StockTransferItem
from apps.products.serializers import StockSerializer, StockMovementSerializer, StockTransferSerializer, StockTransferItemSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.views import BaseViewSet
class StocksViewSet(BaseViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

class StockMovementsViewSet(BaseViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]

class StockTransferViewSet(BaseViewSet):
    queryset = StockTransfer.objects.all()
    serializer_class = StockTransferSerializer
    permission_classes = [IsAuthenticated]
    
class StockTransferItemViewSet(BaseViewSet):
    queryset = StockTransferItem.objects.all()
    serializer_class = StockTransferItemSerializer
    permission_classes = [IsAuthenticated]
