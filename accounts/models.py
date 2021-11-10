from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
from django.db.models.fields import EmailField
# Create your models here.


class MyAccountManager(BaseUserManager):
    def create_user(self,first_name,last_name,username,email,phonenumber=None,password=None):
        if not email:
            raise ValueError('User must have a email address')
        if not username:
            raise ValueError('User must have a username')
        user= self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            phonenumber=phonenumber,
            
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self,first_name,last_name,email,username,password,**other_fields):
        user=self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        
           
        )
        user.is_admin=True
        user.is_active=True
        user.is_staff=True
        user.is_superadmin=True
        user.save(using=self._db)
        return user
class Account(AbstractBaseUser):
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    username=models.CharField(max_length=50,unique=True)
    email=models.EmailField(max_length=100,unique=True)
    phonenumber=models.CharField(max_length=20,null=True, blank=True,unique=True)
    
   
    date_joined=models.DateTimeField(auto_now_add=True)
    last_login=models.DateTimeField(auto_now_add=True)
    is_admin=models.BooleanField(default=False)
    is_staff=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    is_superadmin=models.BooleanField(default=False)

    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['username','first_name','last_name']
    objects=MyAccountManager()
    def __str__(self):
        return self.email
    def has_perm(self, perm, obj=None):
        return self.is_admin
    def has_module_perms(self,add_label):
        return True

class UserProfile(models.Model):
    user=models.OneToOneField(Account,on_delete=models.CASCADE)
    address_line_1=models.CharField(blank=True,max_length=100)
    address_line_2=models.CharField(blank=True,max_length=100)
    profile_picture=models.ImageField(blank=True,upload_to='userprofile')
    city=models.CharField(blank=True,max_length=20)
    state=models.CharField(blank=True,max_length=20)
    country=models.CharField(blank=True,max_length=20)
    def __str__(self):
        return self.user.first_name
    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

class UserAddressBook(models.Model):
    user=models.ForeignKey(Account,on_delete=models.CASCADE)
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    phone=models.CharField(max_length=15)
    email=models.CharField(max_length=50)
    address_line_1=models.CharField(max_length=100)
    address_line_2=models.CharField(max_length=100,blank=True)
    country=models.CharField(max_length=50)
    state=models.CharField(max_length=50)
    city=models.CharField(max_length=50)
    status=models.BooleanField(default=False)