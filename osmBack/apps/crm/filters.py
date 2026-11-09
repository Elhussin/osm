# filters.py

import django_filters
from .models import Customer

class CustomerFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    phone = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="icontains")
    customer_type = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'email', 'customer_type']

