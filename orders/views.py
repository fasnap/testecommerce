from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from accounts.forms import AddressBookForm
from accounts.models import UserAddressBook
from carts.models import BuynowItem, CartItem
from coupons.models import Coupons as Coupon
from coupons.models import CouponCheck
from store.models import Product
from .models import Order, OrderProduct, Payment
from .forms import OrderForm
import datetime
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# Create your views here.
def payments(request):
    body = json.loads(request.body)
    order=Order.objects.get(user=request.user,is_ordered=False,order_number=body['orderID'])
    
    #store transaction detials inside payment model
    payment=Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()
    order.payment=payment
    order.is_ordered=True
    order.save()
    if 'coupon_id' in request.session:
        coupon_id=request.session['coupon_id']
        coupon=Coupon.objects.get(id=coupon_id)
        CouponCheck.objects.create(user=request.user, coupon=coupon)
        
        del request.session['coupon_id']
        del request.session['sub_total']
        del request.session['discount_price']

    #move the cart items to order product table
    cart_items=CartItem.objects.filter(user=request.user)
    for item in cart_items:
        orderproduct=OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment=payment
        orderproduct.user_id=request.user.id
        orderproduct.product_id=item.product_id
        orderproduct.quantity=item.quantity
        orderproduct.product_price=item.product.price
        orderproduct.ordered=True
        orderproduct.save()
        cart_item=CartItem.objects.get(id=item.id)
        product_variation=cart_item.variations.all()
        orderproduct=OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()
        
        #reduce quantity of sold product
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    #clear cart
    CartItem.objects.filter(user=request.user).delete()
    data={
        'order_number': order.order_number,
        'transID':payment.payment_id,
    }
    return JsonResponse(data)

#place order 
def place_order(request,total=0,quantity=0):
    current_user=request.user 
    cart_items=CartItem.objects.filter(user=current_user)
    cart_count=cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    else:
        grand_total=0
        tax=0
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax=(2*total)/100
        pre_grand_total=total + tax
     
    if 'coupon_id' in request.session:
        discount = request.session['discount_price']
        grand_total = request.session['sub_total']   
    else:
        discount = 0
        grand_total = pre_grand_total
    if request.method == 'POST':
        form=OrderForm(request.POST)
        if form.is_valid():
            data=Order()
            data.user=current_user
            data.first_name=form.cleaned_data['first_name']
            data.last_name=form.cleaned_data['last_name']
            data.phone=form.cleaned_data['phone']
            data.email=form.cleaned_data['email']
            data.address_line_1=form.cleaned_data['address_line_1']
            data.address_line_2=form.cleaned_data['address_line_2']
            data.country=form.cleaned_data['country']
            data.state=form.cleaned_data['state']
            data.city=form.cleaned_data['city']
            data.order_note=form.cleaned_data['order_note']
            data.order_total=grand_total
            data.tax=tax
            data.discount=discount
            data.ip=request.META.get('REMOTE_ADDR')
            data.save()

            #generate order number
            yr=int(datetime.date.today().strftime('%Y'))
            dt=int(datetime.date.today().strftime('%d'))
            mt=int(datetime.date.today().strftime('%m'))
            d=datetime.date(yr,mt,dt)
            current_date=d.strftime("%Y%m%d")
            order_number=current_date + str(data.id)
            data.order_number=order_number
            data.save()
            order=Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context={
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'discount':discount,
                'tax':tax,
                'grand_total': grand_total,
            }
            return render(request,'payments.html',context)
        else:
            return redirect('checkout')
    else:
        return redirect('checkout')
    
#order complete
def order_complete(request):
    order_number=request.GET.get('order_number')
    print('order_number',order_number)
    transID=request.GET.get('payment_id')
    try:
        order=Order.objects.get(order_number=order_number,is_ordered=True)
        print('order',order)
        ordered_products=OrderProduct.objects.filter(order=order)
        subtotal=0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity
        payment=Payment.objects.get(payment_id=transID)
        context= {
            'order':order,
            'ordered_products':ordered_products,
            'order_number':order.order_number,
            'transID':payment.payment_id,
            'payment':payment,
            'subtotal':subtotal,
        }
        return render(request,'order_complete.html',context)
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('home')

#user cancel order
def order_cancel(request,orderProduct_id):
    cancel_order = OrderProduct.objects.get(id=orderProduct_id)
    Product.objects.filter(id=cancel_order.product.id).update(stock=cancel_order.product.stock + cancel_order.quantity)
    OrderProduct.objects.filter(id=orderProduct_id).update(status="Cancelled")
    return redirect('my_orders')

#user return product
def order_return(request,orderProduct_id):
    cancel_order = OrderProduct.objects.get(id=orderProduct_id)
    Product.objects.filter(id=cancel_order.product.id).update(stock=cancel_order.product.stock + cancel_order.quantity)
    OrderProduct.objects.filter(id=orderProduct_id).update(status="Returned")
    return redirect('my_orders')

#buynow placeorder
@never_cache
@login_required(login_url = 'user_login')
def buynow_place_order(request, total=0, quantity=0):
    current_user=request.user 
    buynow_items=BuynowItem.objects.filter(user=current_user)
    grand_total=0
    tax=0
    discount=0
    for buynow_item in buynow_items:
        total += (buynow_item.product.price * buynow_item.quantity)
        quantity += buynow_item.quantity
    tax=(2*total)/100
    pre_grand_total=total + tax
    if 'coupon_id' in request.session:
        discount = request.session['discount_price']
        grand_total = request.session['sub_total']   
    else:
        discount = 0
        grand_total = pre_grand_total
    if request.method == 'POST':
        form=OrderForm(request.POST)
        if form.is_valid():
            data=Order()
            data.user=current_user
            data.first_name=form.cleaned_data['first_name']
            data.last_name=form.cleaned_data['last_name']
            data.phone=form.cleaned_data['phone']
            data.email=form.cleaned_data['email']
            data.address_line_1=form.cleaned_data['address_line_1']
            data.address_line_2=form.cleaned_data['address_line_2']
            data.country=form.cleaned_data['country']
            data.state=form.cleaned_data['state']
            data.city=form.cleaned_data['city']
            data.order_note=form.cleaned_data['order_note']
            data.order_total=grand_total
            data.tax=tax
            data.discount=discount
            data.ip=request.META.get('REMOTE_ADDR')
            data.save()
            #generate order number
            yr=int(datetime.date.today().strftime('%Y'))
            dt=int(datetime.date.today().strftime('%d'))
            mt=int(datetime.date.today().strftime('%m'))
            d=datetime.date(yr,mt,dt)
            current_date=d.strftime("%Y%m%d")
            order_number=current_date + str(data.id)
            data.order_number=order_number
            data.save()
           
            order=Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context={
                'order': order,
                'cart_items': buynow_items,
                'total': total,
                'discount':discount,
                'tax':tax,
                'grand_total': grand_total,
            }
            return render(request,'buynow_payments.html',context)
        else:
            return redirect('buy_now')
    else:
        return redirect('buy_now')

#buynow payment
@never_cache
@login_required(login_url = 'user_login')
def buynow_payments(request):
    body = json.loads(request.body)
    order=Order.objects.get(user=request.user,is_ordered=False,order_number=body['orderID'])
    
    #store transaction detials inside payment model
    payment=Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()
    order.payment=payment
    order.is_ordered=True
    order.save()
    if 'coupon_id' in request.session:
        coupon_id=request.session['coupon_id']
        coupon=Coupon.objects.get(id=coupon_id)
        CouponCheck.objects.create(user=request.user, coupon=coupon)
        del request.session['coupon_id']
        del request.session['sub_total']
        del request.session['discount_price']
    
    #move the cart items to order product table
    buynow_items=BuynowItem.objects.filter(user=request.user)
    for item in buynow_items:
        orderproduct=OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment=payment
        orderproduct.user_id=request.user.id
        orderproduct.product_id=item.product_id
        orderproduct.quantity=item.quantity
        orderproduct.product_price=item.product.price
        orderproduct.ordered=True
        orderproduct.save()
        buynow_item=BuynowItem.objects.get(id=item.id)
        product_variation=buynow_item.variations.all()
        orderproduct=OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()
        
        #reduce quantity of sold product
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    #clear cart
    BuynowItem.objects.filter(user=request.user).delete()

    #send order number and trasaction id back to sendData method vis json response 
    data={
        'order_number': order.order_number,
        'transID':payment.payment_id,
    }
    return JsonResponse(data)

#buynoe oder complete
@never_cache
@login_required(login_url = 'user_login')
def buynow_order_complete(request):
    print("payment")
    order_number=request.GET.get('order_number')
    print('order_number',order_number)
    transID=request.GET.get('payment_id')
    try:
        order=Order.objects.get(order_number=order_number,is_ordered=True)
        print('order',order)
        ordered_products=OrderProduct.objects.filter(order=order)
        subtotal=0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity
        payment=Payment.objects.get(payment_id=transID)
        context= {
            'order':order,
            'ordered_products':ordered_products,
            'order_number':order.order_number,
            'transID':payment.payment_id,
            'payment':payment,
            'subtotal':subtotal,
        }
        return render(request,'order_complete.html',context)
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('home')