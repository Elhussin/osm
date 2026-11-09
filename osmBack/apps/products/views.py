from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import ProductVariant
from .serializers.product import ProductVariantSerializer
from apps.crm.models import Customer
# from apps.branches.models import Branch
# from .models import Supplier
# from .serializers.supplier import SupplierSerializer

class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related(
        'product'
    ).prefetch_related('images')
    
    serializer_class = ProductVariantSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', None)

        queryset = self.queryset

        if query:
            queryset = queryset.filter(
                Q(product__name__icontains=query) |
                Q(product__model__icontains=query) |
                Q(product__brand__name__icontains=query) |
                Q(sku__icontains=query)
            )

        if category:
            queryset = queryset.filter(product__categories__id=category)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='calculate-price')
    def calculate_price(self, request, pk=None):
        variant = self.get_object()
        customer_id = request.data.get('customer_id')
        branch_id = request.data.get('branch_id')
        quantity = request.data.get('quantity', 1)

        price = variant.get_price_for(
            customer=Customer.objects.get(pk=customer_id) if customer_id else None,
            branch=Branch.objects.get(pk=branch_id) if branch_id else None,
            quantity=quantity
        )

        return Response({
            'variant_id': variant.id,
            'original_price': variant.selling_price,
            'final_price': price,
            'currency': 'SAR'
        }, status=status.HTTP_200_OK)


