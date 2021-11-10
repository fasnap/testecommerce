from django import forms
from django.forms.widgets import TextInput
from accounts.models import Account
from carts.models import Cart, CartItem
from store.models import Product, Variation
from category.models import Category
class CategoryForm(forms.ModelForm):
    class Meta:
        model=Category        
        fields='__all__'

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product
        fields=['category','product_name','slug','description','actual_price','offer','stock','product_image1','product_image2','product_image3']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'productnameclass'}),
        }
class UserForm(forms.ModelForm):
    class Meta:
        model=Account
        fields='__all__'
    
class VariationForm(forms.ModelForm):
    class Meta:
        model=Variation
        fields='__all__'

