from django.contrib import admin
from django.utils.html import format_html
from .models import Account, UserAddressBook, UserProfile
from django.contrib.auth.admin import UserAdmin
# Register your models here.
class AccountAdmin(UserAdmin):
    list_display=('email','first_name','last_name','username','last_login','date_joined','is_active')

class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self,object):
        return format_html('<img src="{}" width="30" style="border-radius:50% ;">' .format(object.profile_picture.url))
    thumbnail.short_description='Profile Picture'
    list_display=('thumbnail','user','city','state','country')

class UserAddressBookAdmin(admin.ModelAdmin):
    list_display=('user','first_name','last_name','phone','email','address_line_1','address_line_2','country','state','city','status')

admin.site.register(Account)
admin.site.register(UserProfile,UserProfileAdmin)

admin.site.register(UserAddressBook,UserAddressBookAdmin)
