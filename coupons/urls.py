
from django.urls import path
from . import views

urlpatterns = [
    path('checkCoupon/', views.checkCoupon, name="checkCoupon"),
    path('coupon_manage/',views.coupon_manage,name='coupon_manage'),
    path('edit_coupon/<id>/',views.edit_coupon,name='edit_coupon'),
    path('delete_coupon/<id>/',views.delete_coupon,name='delete_coupon'),
    path('addCoupon/',views.addCoupon,name='addCoupon')
]
