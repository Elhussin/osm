# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import ProductVariant
from .helper_functions import (
    get_variant_stock_summary,
    find_nearest_branch_with_stock,
    can_fulfill_order_across_branches
)


class VariantStockSummaryAPIView(APIView):
    def get(self, request, variant_id):
        variant = get_object_or_404(ProductVariant, id=variant_id)
        summary = get_variant_stock_summary(variant)
        return Response(summary)


class NearestBranchAPIView(APIView):
    def get(self, request, variant_id):
        variant = get_object_or_404(ProductVariant, id=variant_id)

        # لاحقًا يمكن استخراج الموقع من الطلب
        user_location = None  
        min_quantity = int(request.query_params.get("min_quantity", 1))
        
        branch_inventory = find_nearest_branch_with_stock(variant, user_location, min_quantity)
        if not branch_inventory:
            return Response({'detail': 'No branch has sufficient stock.'}, status=status.HTTP_404_NOT_FOUND)
        
        data = {
            'branch_id': branch_inventory.branch.id,
            'branch_name': branch_inventory.branch.name,
            'available': branch_inventory.available_quantity,
        }
        return Response(data)


class OrderFulfillmentCheckAPIView(APIView):
    def post(self, request):
        """
        Expecting JSON in the format:
        {
            "items": [
                {"variant_id": 1, "quantity": 3},
                {"variant_id": 5, "quantity": 2}
            ]
        }
        """
        items_data = request.data.get("items", [])
        items_dict = {}

        for item in items_data:
            variant_id = item.get("variant_id")
            quantity = item.get("quantity")
            if not variant_id or not quantity:
                continue
            
            variant = get_object_or_404(ProductVariant, id=variant_id)
            items_dict[variant] = quantity

        fulfillment_plan = can_fulfill_order_across_branches(items_dict)
        
        if not fulfillment_plan:
            return Response({'detail': 'Cannot fulfill order completely.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # تنسيق البيانات للعرض
        response_data = {}
        for variant, plan in fulfillment_plan.items():
            response_data[variant.id] = [
                {
                    'branch_id': item['branch'].id,
                    'branch_name': item['branch'].name,
                    'quantity': item['quantity']
                }
                for item in plan
            ]

        return Response(response_data)
