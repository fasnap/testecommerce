

import re
from threading import current_thread
from django.contrib import messages

from decouple import config
from django.contrib.messages.api import success
# verification email
from django.core.mail import message, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.http.response import JsonResponse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from accounts.admin import UserAddressBookAdmin
from admin1.views import product
from coupons.models import CouponCheck
from coupons.models import Coupons as Coupon
from orders.models import Order, OrderProduct
from .forms import AddressBookForm, RegistrationForm,UserForm,UserProfileForm
from django.contrib.auth.decorators import login_required
from .models import Account, UserAddressBook, UserProfile
from carts.views import _cart_id
from category.models import Category
from store.models import Product
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import auth
from twilio.rest import Client
from carts.models import Cart, CartItem
import requests
from django.views.decorators.cache import never_cache

# Create your views here.
def home(request):
    categorys=Category.objects.all()
    products = Product.objects.all().filter(is_available=True)
    return render(request,'home.html',{'products':products,'categorys':categorys})

#user registration
def register(request):
    if request.method == 'POST':
        form=RegistrationForm(request.POST)  
        print(form)
        if form.is_valid():
            print(form)
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            phonenumber=form.cleaned_data['phonenumber']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            confirm_password=form.cleaned_data['confirm_password']
            username=email.split("@")[0]
            # user=Account.objects.create_user(first_name=first_name,last_name=last_name,email=email,phonenumber=phonenumber,username=username,password=password)
            # user.save()
            # #create user profile
            # profile=UserProfile()
            # profile.user_id=user.id
            # profile.save()
            request.session['first_name'] = first_name
            request.session['last_name'] = last_name
            request.session['username'] = username
            request.session['email'] = email
            request.session['phonenumber'] = phonenumber
            request.session['password'] = password
            request.session['confirm_password'] = confirm_password
            if password == confirm_password:
               
                if Account.objects.filter(email=email).exists():
                    messages.error(request,'Email already taken')
                    return render(request,'register.html')
                elif Account.objects.filter(phonenumber=phonenumber).exists():
                    messages.error(request,'Phone number already taken')
                    return render(request,'register.html')
                else:
                    try:
                        account_sid = config('account_sid')
                        auth_token = config('auth_token')
                        client = Client(account_sid, auth_token)

                        verification = client.verify \
                            .services('VA92be102e4eec0ddab0c97446a26a3c53') \
                            .verifications \
                            .create(to='+91'+phonenumber, channel='sms')
                        return redirect('reg_otp')
                    except:
                        messages.info(request,'Enter valid mobile number')
                        return redirect('register')
            else:
                messages.error(request,'Password is not matching')
                return render(request,'register.html')
        

    else:
        form=RegistrationForm()
    
    context={
        'form':form,
    }
    return render(request,'register.html',context)

# registration OTP
@never_cache
def reg_otp(request):
    if request.method == 'POST':
        otp = request.POST['otp']

        phonenumber = request.session['phonenumber']

        account_sid = config('account_sid')
        auth_token = config('auth_token')
        client = Client(account_sid, auth_token)

        verification_check = client.verify \
            .services('VA92be102e4eec0ddab0c97446a26a3c53') \
            .verification_checks \
            .create(to='+91'+phonenumber, code=otp)

        print(verification_check.status)

        if verification_check.status == 'approved':
            first_name = request.session['first_name']
            last_name = request.session['last_name']
            username = request.session['username']
            email = request.session['email']
            phonenumber = request.session['phonenumber']
            password = request.session['password']

            
            user = Account.objects.create_user(first_name=first_name, last_name=last_name,
                                               username=username, email=email, phonenumber=phonenumber, password=password)
            
            user.save()
            #create user profile
            profile=UserProfile()
            profile.user_id=user.id
            profile.save()
            auth.login(request, user)   
               
           # deleting details in session
            del request.session['last_name']
            del request.session['first_name']
            del request.session['username']
            del request.session['email']
            del request.session['phonenumber']
            del request.session['password']
            return redirect('home')

          
        else:
            messages.info(request, 'OTP is not matching')
            return redirect('reg_otp')
    else:
        return render(request, 'reg_otp.html')









#user login  page
def user_login(request):
    if request.method == 'POST':
        email=request.POST['email']
        password=request.POST['password']
        user=auth.authenticate(email=email,password=password)
        if user is not None:
            
            try:
                cart=Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists=CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item=CartItem.objects.filter(cart=cart)
                    #get product variation with cart id
                    product_variation= []
                    for item in cart_item:
                        variation=item.variations.all()
                        product_variation.append(list(variation))
                    #get cart item from user to acess product variation
                    cart_item=CartItem.objects.filter(user=user)
                    ex_var_list=[]
                    id=[]
                    for item in cart_item:
                        existing_variation=item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    # product_variation=[1,2,3,4]
                    # ex_var_list=[4,6,3,5]
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index=ex_var_list.index(pr)
                            item_id=id[index]
                            item=CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user=user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request,user)
            messages.success(request,'You Are now logged in')
            url=request.META.get('HTTP_REFERER')
            try:
                query=requests.utils.urlparse(url).query
                #next=/cart/checkout/
                params= dict(x.split('=') for x in query.split('&'))
                print('params -> ',params)
                if 'next' in params:
                    nextPage=params['next']
                    return redirect(nextPage)
            except:
                return redirect('user_dashboard')
               
        else:
            messages.error(request,'invalid login credentials')
            return redirect('user_login')
    return render(request,'user_login.html')

#user logout
@login_required(login_url='user_login')
def logout(request):
    auth.logout(request)
    messages.success(request,'You Are logged out')
    return redirect('user_login')

# user - otp to phone
def phone_login(request):
    if request.method == 'POST':
        phonenumber = request.POST['phonenumber']

        if Account.objects.filter(phonenumber=phonenumber):

            request.session['phonenumber'] = phonenumber

            account_sid = config('account_sid')
            auth_token = config('auth_token')
            client = Client(account_sid,auth_token)

            verification = client.verify \
                .services('VA92be102e4eec0ddab0c97446a26a3c53') \
                .verifications \
                .create(to='+91'+phonenumber, channel='sms')

            print(verification.status)
            return redirect('login_otp')

        else:
            messages.info(request, 'Phone Number is not Registered')
            return redirect('phone_login')
    else:

        return render(request, 'phone_login.html')

    
# user otp login
def login_otp(request):
    if request.method == 'POST':
        otp = request.POST['otp']

        phonenumber= request.session['phonenumber']

        account_sid = config('account_sid')
        auth_token = config('auth_token')
        client = Client(account_sid, auth_token)

        verification_check = client.verify \
            .services('VA92be102e4eec0ddab0c97446a26a3c53') \
            .verification_checks \
            .create(to='+91'+phonenumber, code=otp)

        print(verification_check.status)

        if verification_check.status == 'approved':

            user = Account.objects.get(phonenumber=phonenumber)

            if user is not None:
                auth.login(request, user)
                
                print('hi')
                return redirect('home')
                
            else:
                return redirect('login_otp')

        else:
            messages.info(request, 'OTP is not matching')
            return redirect('login_otp')
    else:
        return render(request, 'login_otp.html')

def forgot_password(request):
    if request.method == 'POST':
        phonenumber = request.POST['phonenumber']
    
        if Account.objects.filter(phonenumber=phonenumber):

            request.session['phonenumber'] = phonenumber
            account_sid = config('account_sid')
            auth_token = config('auth_token')
            client = Client(account_sid,auth_token)

            verification = client.verify \
                .services('VA92be102e4eec0ddab0c97446a26a3c53') \
                .verifications \
                .create(to='+91'+phonenumber, channel='sms')

            print(verification.status)
            return redirect('forgotPassOtp')

        else:
            messages.info(request, 'Phone Number is not Registered')
            return redirect('forgot_password')
    return render(request,'forgot_password.html')


def forgotPassOtp(request):
    if request.method == 'POST':
        otp = request.POST['otp']
        phonenumber = request.session['phonenumber']

        account_sid = config('account_sid')
        auth_token = config('auth_token')
        client = Client(account_sid, auth_token)

        verification = client.verify \
            .services('VA92be102e4eec0ddab0c97446a26a3c53') \
            .verification_checks \
            .create(to='+91'+phonenumber, code=otp)

        print(verification.status)
        if verification.status == 'approved':
            return redirect('resetPass')
        else:
            messages.info(request, 'OTP is not matching')
            return redirect('forgotPassOtp')
    else:
        return render(request, 'forgotPassOtp.html')



def resetPass(request):
    if request.method == 'POST':
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1 == password2:
            phonenumber = request.session['phonenumber']
            user = Account.objects.get(phonenumber=phonenumber)
            user.set_password(password1)
            user.save()
            del request.session['phonenumber']
            return redirect('user_login')
        else:
            messages.info(request, 'Password is not matching')
            return redirect('resetPass')
    else:
        return render(request,'resetPass.html')







#user profile order details
@login_required(login_url='user_login')
def my_orders(request):
    order_items=OrderProduct.objects.filter(user=request.user)
    orders=Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
    context={
        'order_items':order_items,
        'orders':orders
    }
    return render(request,'my_orders.html',context)

#User editprofile
@login_required(login_url='user_login')
def edit_profile(request):
    try:
        userprofile = get_object_or_404(UserProfile, user=request.user)
    except:
        userprofile=UserProfile(user=request.user)
        userprofile.save()
    if request.method == 'POST':
        user_form=UserForm(request.POST, instance=request.user)
        profile_form=UserProfileForm(request.POST,request.FILES,instance=userprofile)
        if user_form.is_valid() and  profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,'Your Profile has been Updated')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance = request.user)
        profile_form = UserProfileForm(instance = userprofile)
   
    context={
        'user_form':user_form,
        'profile_form':profile_form,
        'userprofile': userprofile,
    }

    return render(request,'edit_profile.html',context)


#User dashboard profile
@login_required(login_url = 'user_login')
def user_dashboard(request):
    orders=Order.objects.order_by('-created_at').filter(user_id=request.user.id,is_ordered=True)
    orders_count=orders.count()
    try:
        userprofile=UserProfile.objects.get(user_id=request.user.id)
    except:
        userprofile=UserProfile(user=request.user)
        userprofile.save()
    context={
        'orders_count':orders_count,
        'userprofile': userprofile,
    }
    return render(request,'user_dashboard.html',context)

#Change password from user profile
@login_required(login_url='user_login')
def change_password(request):
    if request.method == 'POST':
        current_password=request.POST['current_password']
        new_password=request.POST['new_password']
        confirm_password=request.POST['confirm_password']
        user=Account.objects.get(username__exact=request.user.username)
        if new_password == confirm_password:
            success=user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                #auth.logout request
                messages.success(request,'password updated successfully')
                return redirect('change_password')
            else:
                messages.error(request,'please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request,'password does not match')
            return redirect('change_password')
    return render(request,'change_password.html')

#Order details in user profile
def order_detail(request,order_id):
    order_detail=OrderProduct.objects.filter(order__order_number=order_id)
    order=Order.objects.get(order_number=order_id)
    subtotal=0
    for i in order_detail:
        subtotal += i.product_price * i.quantity
    context={
        'order_detail':order_detail,
        'order':order,
        'subtotal': subtotal ,
    }
    return render(request,'order_detail.html',context)

#Profile Address book 
def address_book(request):
    print("address")
    addbook=UserAddressBook.objects.filter(user=request.user)
    return render(request,'address_book.html',{'addbook':addbook})

#save addressbook
def save_address(request):
    msg=None
    if request.method == 'POST':
        form=AddressBookForm(request.POST)
        if form.is_valid():
            saveForm=form.save(commit=False)
            saveForm.user=request.user
            saveForm.save()
            msg='Data has been saved successfully'
            return redirect('address_book')
    form=AddressBookForm
    return render(request,'add-address.html',{'form':form,'msg':msg})

#address activate
def activate_address(request):
    a_id=str(request.GET['id'])
    UserAddressBook.objects.update(status=False)
    UserAddressBook.objects.filter(id=a_id).update(status=True)
    return JsonResponse({'bool':True})

#Delete Address
def delete_address(request,id):
    UserAddressBook.objects.filter(id=id).delete()
    return redirect('checkout')

#Delete Address
def delete_address_user(request,id):
    UserAddressBook.objects.filter(id=id).delete()
    return redirect('address_book')




#Adress in checkout
def save_address_checkout(request): 
    msg=None
    if request.method=='POST': 
        form=AddressBookForm(request.POST)
        if form.is_valid():
            saveForm=form.save(commit=False)
            saveForm.user=request.user
            saveForm.save()
            msg='Data has been saved successfully'
            return redirect('checkout')
    form=AddressBookForm()
    return render(request,'add-address.html',{'form':form,'msg':msg})









def activate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=Account._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,Account.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(request,'congrats')
        return redirect('login')
    else:
        messages.error(request,'invalid link')
        return redirect('register')
