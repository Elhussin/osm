# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.branches.models import Branch
from .models import Stock, ProductVariant
from apps.branches.serializers import BranchSerializer
from .serializers.inventory import StockSerializer # Assuming StockSerializer replaced BranchInventorySerializer
from django.db.models import F, Sum

class ActiveBranchesView(APIView):
    def get(self, request):
        branches = Branch.objects.filter(is_active=True) # Assuming active() manager or filter
        return Response(BranchSerializer(branches, many=True).data)


class MainBranchView(APIView):
    def get(self, request):
        branch = Branch.objects.filter(is_main=True).first() # Assuming is_main flag
        if not branch:
             return Response({})
        return Response(BranchSerializer(branch).data)


class LowStockByBranchView(APIView):
    def get(self, request, branch_id):
        # inventories = BranchInventory.objects.for_branch(branch_id).low_stock()
        # Stock status logic: available <= reorder_level
        # available = quantity - reserved
        # So: quantity - reserved <= reorder_level
        # This requires F expression
        inventories = Stock.objects.filter(
            branch_id=branch_id, 
            quantity_in_stock__lte=F('reorder_level') + F('reserved_quantity')
        )
        return Response(StockSerializer(inventories, many=True).data)


class VariantTotalStockView(APIView):
    def get(self, request, variant_id):
        variant = ProductVariant.objects.get(id=variant_id)
        # total_stock = BranchInventory.objects.get_total_stock(variant)
        total_stock = Stock.objects.filter(variant=variant).aggregate(total=Sum('quantity_in_stock'))['total'] or 0
        return Response({'variant': variant.id, 'total_stock': total_stock})
