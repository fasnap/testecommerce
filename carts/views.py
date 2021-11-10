from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import DateField
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from accounts.models import UserAddressBook
from admin1.views import status
from coupons.models import Coupons as Coupon
from .models import BuynowItem, CartItem,Cart
from store.models import Product, Variation
from django.views.decorators.cache import never_cache
import math
#  Create your views here.


def _cart_id(request):   #private function-pep8 standard
    cart=request.session.session_key
    if not cart:
        cart=request.session.create()
    return cart


def add_cart(request,product_id):
    current_user=request.user
    product=Product.objects.get(id=product_id)
    if current_user.is_authenticated:
        product_variation=[]
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value =  request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
        is_cart_item_exists=CartItem.objects.filter(product=product,user=current_user).exists()
        if is_cart_item_exists:
            cart_item=CartItem.objects.filter(product=product,user=current_user)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation=item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            if product_variation in ex_var_list:
                if product.stock <= item.quantity:
                    messages.error(request,'product not available')
                else:
                    # increase cart item quantity
                    index=ex_var_list.index(product_variation)
                    item_id=id[index]
                    item=CartItem.objects.get(product=product,id=item_id)
                    item.quantity += 1
                    item.save()
            else:
                # add new  item to cart
                item=CartItem.objects.create(product=product,quantity=1,user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
            #cart_item.quantity += 1
                item.save()
        else :
            cart_item=CartItem.objects.create(
                product=product,
                quantity=1,
               user=current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
            
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')

    else:
        
        product_variation=[]
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value =  request.POST[key]
                
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
    
        try:
            cart=Cart.objects.get(cart_id=_cart_id(request)) #getthe  cart using the cart_is present in the session
        except Cart.DoesNotExist:
            cart=Cart.objects.create(
                cart_id=_cart_id(request)
            )
        cart.save()
        is_cart_item_exists=CartItem.objects.filter(product=product,cart=cart).exists()

        if is_cart_item_exists:
            cart_item=CartItem.objects.filter(product=product,cart=cart)
            # existing variations -> db
            # current variation -> product_variation
            # item id -> db
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation=item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            print(ex_var_list)

            if product_variation in ex_var_list:

                # increase cart item quantity
                index=ex_var_list.index(product_variation)
                item_id=id[index]
                item=CartItem.objects.get(product=product,id=item_id)
                item.quantity += 1
                item.save()
            else:
                # add new  item to cart
                item=CartItem.objects.create(product=product,quantity=1,cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
            #cart_item.quantity += 1
                item.save()
        else :
            cart_item=CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
            
                cart_item.variations.add(*product_variation)
            cart_item.save()

        return redirect('cart')

def remove_cart(request,product_id,cart_item_id):
    
    product=get_object_or_404(Product,id=product_id)
    try:
        if request.user.is_authenticated:
             cart_item=CartItem.objects.get(product=product, user=request.user,id=cart_item_id)
        else:
            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_item=CartItem.objects.get(product=product, cart=cart,id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request,product_id,cart_item_id):
   
    product=get_object_or_404(Product,id=product_id)
    if request.user.is_authenticated:
         cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
    else:
        cart=Cart.objects.get(cart_id=_cart_id(request))
        cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

def remove_item_cart(request):
    product_id = request.POST['product_id']
    cart_item_id = request.POST['cart_item_id']

    print(product_id)
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
         cart_item=CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
    else:
        cart=Cart.objects.get(cart_id=_cart_id(request))
        cart_item=CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
    cart_item.delete()
    return JsonResponse({'success': True})


def cart(request,total=0,quantity=0,cart_items=None):
    try:
        tax=0
        grand_total=0
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True).order_by('-id')
        else:

            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True).order_by('-id')
        for cart_item in cart_items:
            total+=(cart_item.product.price * cart_item.quantity)
            quantity+=cart_item.quantity
        tax= (2 * total)/100
        grand_total=total+tax
    except ObjectDoesNotExist:
        pass
    context={
        'total' : total,
        'quantity' : quantity,
        'cart_items' : cart_items,
        'tax' : tax,
        'grand_total' : grand_total
    }
    return render(request, 'cart.html', context)
@login_required(login_url='user_login')
def checkout(request,total=0,quantity=0,cart_items=None):


    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        del request.session['sub_total']
        del request.session['discount_price']

        
    address=UserAddressBook.objects.filter(user=request.user)
    
    selectaddress=UserAddressBook.objects.filter(user=request.user,status=True).first()
    try:
        tax=0
        grand_total=0
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True)
        else:

            cart=Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total+=(cart_item.product.price)*cart_item.quantity
            quantity+=cart_item.quantity
        
        tax= (2 * total)/100
        grand_total=total+tax
    except ObjectDoesNotExist:
        pass
    context={
        'selectaddress':selectaddress,
        'address':address,
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'tax':tax,
        'grand_total':grand_total
    }
    return render(request,'checkout.html',context)

@never_cache
@login_required(login_url = 'user_login')
def buy_now(request,id,tax=0, total=0, quantity=0, cart_items=None):
    BuynowItem.objects.all().delete()
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        del request.session['sub_total']
        del request.session['discount_price']
    
    product = Product.objects.get(id=id)
    try:
        # get the cart using the cart id present in the session
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
    cart.save()

    try:
        buynow_item = BuynowItem.objects.get(product=product, user=request.user)
        if buynow_item.quantity > buynow_item.product.stock-1:
            messages.info(request, 'Product Out of Stock')
            return redirect('cart')
        else:
            buynow_item.quantity += 1
            buynow_item.save()


    except BuynowItem.DoesNotExist:
        buynow_item = BuynowItem.objects.create(
            product=product,
            quantity=1,
            user=request.user,
        )
        buynow_item.save()


    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            buynow_items = BuynowItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            buynow_items = BuynowItem.objects.filter(cart=cart, is_active=True)
        for buynow_item in buynow_items:
            total += (buynow_item.product.price * buynow_item.quantity)
            quantity += buynow_item.quantity
        tax = (2*total)/100
        grand_total = total + tax
        grand_total=math.floor(grand_total)

    except ObjectDoesNotExist:
        pass  # just ignore

    addresses = UserAddressBook.objects.filter(user=request.user)

    context = {
        'total': total,
        'quantity': quantity,
        'buynow_items': buynow_items,
        'tax': tax,
        'grand_total': grand_total,
        'addresses': addresses,
    }
    return render(request, 'buy_now_checkout.html', context)