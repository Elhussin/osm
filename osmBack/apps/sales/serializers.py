

from rest_framework import serializers
from apps.sales.models import Order, OrderItem, Invoice, InvoiceItem ,Payment
from apps.products.models import ProductVariant

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['total_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['order_number', 'total_amount', 'subtotal', 'tax_amount', 'confirmed_at', 'delivered_at']

    def validate_items(self, items):
        seen = set()
        for item in items:
            variant_id = item.get('variant') or item.get('product_variant')
            if variant_id in seen:
                raise serializers.ValidationError(f"Duplicate variant in order: {variant_id}")
            seen.add(variant_id)
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        order.calculate_totals()
        return order



class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = '__all__'
        read_only_fields = ['total_price']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = [
            'invoice_number', 'total_amount', 'subtotal', 'tax_amount',
            'created_by', 'status'
        ]

    def validate_items(self, items):
        seen = set()
        for item in items:
            variant_id = item.get('product_variant')
            if variant_id in seen:
                raise serializers.ValidationError(f"Duplicate variant in invoice: {variant_id}")
            seen.add(variant_id)
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        invoice = Invoice.objects.create(**validated_data)
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        invoice.calculate_totals()
        return invoice



class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id']
