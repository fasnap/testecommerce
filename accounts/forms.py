from django import forms
from django.contrib.messages.api import error
from django.db.models import fields
from django.forms.fields import Field
from .models import Account, UserAddressBook, UserProfile

class RegistrationForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Enter password',
        'class':'form-control'
    }))
    confirm_password=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder':'Confirm password'
    }))
    class Meta:
        model=Account
        fields=['first_name','last_name','phonenumber','email','password']
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['phonenumber'].widget.attrs['placeholder'] = 'Enter Phone number'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email'
        for fields in self.fields:
            self.fields[fields].widget.attrs['class'] = 'form-control'
        
    def clean(self):
        cleaned_data=super(RegistrationForm, self).clean()
        password=cleaned_data.get('password')
        confirm_password=cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "Password does not match!"
            )

class UserForm(forms.ModelForm):
    class Meta:
        model=Account
        fields=('first_name','last_name','phonenumber')
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class UserProfileForm(forms.ModelForm):
    profile_picture=forms.ImageField(required=False,error_messages={'invalid':("Image files only")}, widget=forms.FileInput)
    class Meta:
        model=UserProfile
        fields=('address_line_1','address_line_2','city','state','country','profile_picture')
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

class AddressBookForm(forms.ModelForm):
    class Meta:
        model=UserAddressBook
        fields=('first_name','last_name','phone','email','address_line_1','address_line_2','city','state','country')