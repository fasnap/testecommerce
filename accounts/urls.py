
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
  
    path('',views.home,name='home'),
    path('home',views.home,name='home'),
    path('register',views.register,name='register'),
    path('reg_otp',views.reg_otp,name='reg_otp'),
    path('user_login',views.user_login,name='user_login'),
    path('logout',views.logout,name='logout'),
    path('user_dashboard',views.user_dashboard,name='user_dashboard'),
    path('forgot_password',views.forgot_password,name='forgot_password'),
    path('forgotPassOtp',views.forgotPassOtp,name='forgotPassOtp'),
    path('resetPass',views.resetPass,name='resetPass'),
    
    
    
  
  
    # path('forgot_otp',views.forgot_otp,name='forgot_otp'),
    # path('reset_password',views.reset_password,name='reset_password'),
    

    path('phone_login',views.phone_login,name='phone_login'),
    # path('reset_phone_login',views.reset_phone_login,name='reset_phone_login'),
    # path('reset_login_otp',views.reset_login_otp,name='reset_login_otp'),
    path('login_otp',views.login_otp,name='login_otp'),
    path('my_orders/',views.my_orders,name='my_orders'),
    path('edit_profile/',views.edit_profile,name='edit_profile'),
    path('change_password/',views.change_password,name='change_password'),
    path('address_book/',views.address_book,name='address_book'),
    path('add-address/',views.save_address,name='add-address'),
    path('activate-address/',views.activate_address,name='activate-address'),
    path('order_detail/<int:order_id>/',views.order_detail,name='order_detail'),
    path('delete_address/<id>/',views.delete_address,name='delete_address'),
    path('delete_address_user/<id>/',views.delete_address_user,name='delete_address_user'),
    path('save_address_checkout/',views.save_address_checkout,name='save_address_checkout'),
    
]
