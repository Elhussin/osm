
from rest_framework import serializers
from .models import PrescriptionRecord
from apps.crm.serializers import CustomerSerializer
from apps.users.serializers import UserSerializer

class PrescriptionRecordSerializer(serializers.ModelSerializer):

    # customer = CustomerSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    customer_name = serializers.CharField(source="customer.first_name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = PrescriptionRecord
        fields = '__all__'

    def to_internal_value(self, data):
        print (data)
        # # Coerce empty strings to None for nullable fields
        
        for field in [
            'right_sphere', 'right_cylinder', 'right_axis',
            'left_sphere', 'left_cylinder', 'left_axis',
            'right_reading_add', 'left_reading_add',
            'right_pupillary_distance', 'left_pupillary_distance',
            'sigmant_right', 'sigmant_left',
            'a_v_right', 'a_v_left',
            'doctor_name', 'notes',
        ]:
            if field in data and data[field] == "":
                data[field] = None

        if 'customer' in data and isinstance(data['customer'], str) and data['customer'].isdigit():
            data['customer'] = int(data['customer'])


        if 'customer' in data and data['customer'] == "":

            raise serializers.ValidationError({'customer': ['Customer field is required.']})
        

        return super().to_internal_value(data)
