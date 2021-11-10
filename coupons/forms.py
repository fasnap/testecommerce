from django import forms
from .models import Coupons as Coupon
from django.forms import fields, models

class DateInput(forms.DateInput):
    input_type= 'date'

class CouponApplyForm(forms.ModelForm):
    class Meta:
       model = Coupon
       fields=('code','discount','valid_to','valid_from')
       widgets={
           'valid_from' : DateInput(),
           'valid_to' : DateInput(),
       }