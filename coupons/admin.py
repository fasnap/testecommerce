from django.contrib import admin
from .models import Coupons as Coupon
from .models import CouponCheck


admin.site.register(Coupon)
admin.site.register(CouponCheck)
