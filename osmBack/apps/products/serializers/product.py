from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.products.models import (
    Category, Product, ProductVariant, 
    ProductImage, FlexiblePrice,Supplier,Manufacturer,Brand,AttributeValue,
    Attribute
)
from apps.crm.models import Customer,CustomerGroup
from apps.branches.models import Branch, BranchUsers
from apps.crm.serializers import CustomerGroupSerializer
from apps.branches.serializers import BranchSerializer
from apps.products.serializers.attributes import AttributeValueSerializer
from apps.products.serializers.suppliers import SupplierSerializer, ManufacturerSerializer, BrandSerializer
from apps.products.serializers.inventory import StockMovementSerializer,StockSerializer,StockTransferSerializer, StockTransferItemSerializer

class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)

    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            'id', 'variant', 'image', 'alt_text', 
            'order', 'is_primary'
        ]
        read_only_fields = ['id', ]
        extra_kwargs = {
            'image': {'required': True}
        }



class ProductVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductVariant
        fields = '__all__'
        read_only_fields = [
            'id', 'usku', 'discount_price', 'images',
            'created_at', 'updated_at', 'product'
        ]

class FrameVariantSerializer(ProductVariantSerializer):
    frame_shape_name = serializers.CharField(source='frame_shape.name', read_only=True)
    frame_material_name = serializers.CharField(source='frame_material.name', read_only=True)
    frame_color_name = serializers.CharField(source='frame_color.name', read_only=True)
    temple_length_name = serializers.CharField(source='temple_length.name', read_only=True)
    bridge_width_name = serializers.CharField(source='bridge_width.name', read_only=True)

class StokLensVariantSerializer(ProductVariantSerializer):
    pass
    # spherical_name = serializers.CharField(source='spherical.name', read_only=True)
    # cylinder_name = serializers.CharField(source='cylinder.name', read_only=True)

# variants/rx_lens.py
class RxLensVariantSerializer(ProductVariantSerializer):
    addition_name = serializers.CharField(source='addition.name', read_only=True)
    lens_base_curve_name = serializers.CharField(source='lens_base_curve.name', read_only=True)


class ContactLensVariantSerializer(ProductVariantSerializer):
    lens_base_curve_name = serializers.CharField(source='lens_base_curve.name', read_only=True)
    lens_water_content_name = serializers.CharField(source='lens_water_content.name', read_only=True)
    replacement_schedule_name = serializers.CharField(source='replacement_schedule.name', read_only=True)
    lens_color_name = serializers.CharField(source='lens_color.name', read_only=True)
    lens_material_name = serializers.CharField(source='lens_material.name', read_only=True)



class ContactLensVariantExpirationDateSerializer(ProductVariantSerializer):
    pass

class ExtraVariantAttributeSerializer(ProductVariantSerializer):
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all()
    )
    attribute = serializers.PrimaryKeyRelatedField(
        queryset=Attribute.objects.all()
    )
    value = serializers.PrimaryKeyRelatedField(
        queryset=AttributeValue.objects.all()
    )

class FlexiblePriceSerializer(serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all()
    )
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        allow_null=True
    )
    customer_group = CustomerGroupSerializer(read_only=True)
    customer_group_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomerGroup.objects.all(),
        source='customer_group',
        write_only=True,
        allow_null=True
    )
    branch = BranchSerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        source='branch',
        write_only=True,
        allow_null=True
    )
    
    class Meta:
        model = FlexiblePrice
        fields = [
            'id', 'variant', 'customer', 'customer_group', 'customer_group_id',
            'branch', 'branch_id', 'special_price', 'start_date', 'end_date',
            'min_quantity', 'currency', 'priority'
        ]
    
    def validate(self, data):
        # Ensure either customer or customer_group is set, not both
        if data.get('customer') and data.get('customer_group'):
            raise serializers.ValidationError(
                "Cannot set both customer and customer group."
            )
        
        # Validate date range
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    "End date must be after start date."
                )
        
        return data
    
    
class ProductVariantOfferSerializer (serializers.ModelSerializer):
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all()
    )
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        allow_null=True
    )
    customer_group = CustomerGroupSerializer(read_only=True)
    customer_group_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomerGroup.objects.all(),
        source='customer_group',
        write_only=True,
        allow_null=True
    )
    branch = BranchSerializer(read_only=True)
    branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        source='branch',
        write_only=True,
        allow_null=True
    )   



VARIANT_SERIALIZER_MAPPING = {
    "basic": ProductVariantSerializer,
    "frames": FrameVariantSerializer,
    "StockLenses": StokLensVariantSerializer,
    "RxLenses": RxLensVariantSerializer,
    "ContactLenses": ContactLensVariantSerializer,
    "ContactLensesExpirationDate": ContactLensVariantExpirationDateSerializer,
    "custom": ExtraVariantAttributeSerializer,
}

class ProductSerializer(serializers.ModelSerializer):
    manufacturer_name = serializers.CharField(source='manufacturer.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    type = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()  # 👈 ديناميكي حسب variant_type

    def get_type(self, obj):
        return obj.get_type_display()

    def get_variants(self, obj):
        serializer_class = VARIANT_SERIALIZER_MAPPING.get(obj.variant_type, ProductVariantSerializer)
        variants_qs = obj.variants.all()
        return serializer_class(variants_qs, many=True, context=self.context).data

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'description', 'usku']

    def create(self, validated_data):
        variants_data = validated_data.pop('variants', [])
        product = Product(**validated_data)
        product.save()

        # إنشاء الـ variants حسب نوع المنتج
        for vdata in variants_data:
            ProductVariant.objects.create(product=product, **vdata)

        return product

    def update(self, instance, validated_data):
        variants_data = validated_data.pop('variants', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        existing_variant_ids = [v.id for v in instance.variants.all()]
        sent_variant_ids = [v.get('id') for v in variants_data if v.get('id')]

        # حذف أي variant غير موجود
        for variant in instance.variants.all():
            if variant.id not in sent_variant_ids:
                variant.delete()

        # إنشاء أو تحديث الـ variants
        for vdata in variants_data:
            variant_id = vdata.get('id')
            if variant_id and variant_id in existing_variant_ids:
                variant = ProductVariant.objects.get(id=variant_id, product=instance)
                for attr, value in vdata.items():
                    setattr(variant, attr, value)
                variant.save()
            else:
                ProductVariant.objects.create(product=instance, **vdata)

        return instance

