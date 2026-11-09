# # filters.py

# import django_filters
# from .models import Customer, Product, Invoice, Order

# class CustomerFilter(django_filters.FilterSet):
#     name = django_filters.CharFilter(lookup_expr="icontains")
#     phone = django_filters.CharFilter(lookup_expr="icontains")
#     email = django_filters.CharFilter(lookup_expr="icontains")

#     class Meta:
#         model = Customer
#         fields = ['name', 'phone', 'email']


# class ProductFilter(django_filters.FilterSet):
#     name = django_filters.CharFilter(lookup_expr="icontains")
#     category = django_filters.CharFilter(lookup_expr="iexact")
#     color = django_filters.CharFilter(lookup_expr="iexact")

#     class Meta:
#         model = Product
#         fields = ['name', 'category', 'color']


# class InvoiceFilter(django_filters.FilterSet):
#     number = django_filters.CharFilter(lookup_expr="icontains")
#     customer = django_filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
#     status = django_filters.ChoiceFilter(choices=[('paid', 'مدفوعة'), ('unpaid', 'غير مدفوعة')])

#     class Meta:
#         model = Invoice
#         fields = ['number', 'customer', 'status']
# views.py

# from django_filters.rest_framework import DjangoFilterBackend

# class CustomerViewSet(ModelViewSet):
#     queryset = Customer.objects.all()
#     serializer_class = CustomerSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = CustomerFilter


# class ProductViewSet(ModelViewSet):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_class = ProductFilter
