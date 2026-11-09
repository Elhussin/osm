from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        # widgets = {
        #     'name': forms.TextInput(attrs={'class': 'form-control'}),
        #     'description': forms.Textarea(attrs={'class': 'form-control'}),
        #     'price': forms.NumberInput(attrs={'class': 'form-control'}),
        #     'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        # }
        # labels = {
        #     'name': 'Product Name',
        #     'description': 'Description',
        #     'price': 'Price',
        #     'stock': 'Stock Quantity',
        # }
        # help_texts = {
        #     'name': 'Enter the name of the product.',
        #     'description': 'Provide a detailed description of the product.',
        #     'price': 'Set the price for the product.',
        #     'stock': 'Specify the available stock quantity.',
        # }
