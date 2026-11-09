# from Learn.scripts.python.json_to_csv import f
from rest_framework import serializers
from apps.products.models import Attribute, AttributeValue


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    class Meta:
        model = AttributeValue
        fields = '__all__'
        # fields = ['id', 'value', 'attribute', 'attribute_name']
        

class AttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        # fields = ['id', 'name', 'values']
        fields = '__all__'

