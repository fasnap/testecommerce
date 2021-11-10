from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.base import ContentFile
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models.aggregates import Count
from django.http import request, response,HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.models import auth
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import encoding
from accounts.models import Account
from django.db.models.functions import ExtractMonth, datetime
from category.models import Category
from coupons.models import Coupons as Coupon
from orders.models import Order, OrderProduct
from .forms import  CategoryForm,ProductForm,VariationForm
from category.models import Category
from store.models import Product, ReviewRating, Variation
from django.shortcuts import render  
import calendar
from django.db.models import Q
import csv
from weasyprint import HTML
import tempfile
import xlwt

#admin login check 
def logincheck(request):
    if request.method=='POST':
        email=request.POST['email']
        password=request.POST['password']
        user=auth.authenticate(email=email,password=password)
        if user is not None:
            if user.is_superadmin == True:
                auth.login(request,user)
                return redirect('dashboard')
            else:
                messages.info(request,'Invalid username and password')
                return redirect('login')
        else:
            messages.info(request,'Invalid username and password')
            return redirect('login')
    else:
        return redirect('login')

#admin login
def login(request):
    return render(request,'admin/login.html')

#admin logout
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def adminlogout(request):
    auth.logout(request)
    request.session.flush()
    return redirect('logincheck')

#admin home page 
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def dashboard(request):
    labels = []
    data = []
    orders=OrderProduct.objects.annotate(month=ExtractMonth('created_at')).values('month').annotate(count=Count('id')).values('month','count')
    monthNumber=['july','auguest','september']
    totalOrders=[0,0,0]
    for d in orders:
        monthNumber.append(calendar.month_name[d['month']])
        totalOrders.append([d['count']])
    queryset = Product.objects.order_by('-price')[:5]
    for product in queryset:
        labels.append(product.product_name)
        data.append(product.price)
    user_count=Account.objects.count()
    product_count=Product.objects.count()
    cat_count=Category.objects.count()
    product_date = Product.objects.order_by('-id')[1]
    p_date = product_date.modified_date.date()
    p_day = product_date.modified_date.strftime("%A")
    category_date = Category.objects.order_by('-id')[1]
    c_date =  category_date.modified_date.date()
    c_day =  category_date.modified_date.strftime("%A")
    user_date = Account.objects.get(email=request.user)
    u_date =  user_date.last_login.date
    u_day =user_date.last_login.strftime("%A")
    products=Product.objects.all().filter(is_available=True).order_by('-price')[:3]
    categories=Category.objects.all()
    context={
        'categories':categories,
        'products':products,
        'monthNumber':monthNumber,
        'totalOrders':totalOrders,
        'orders':orders,
        'labels':labels,
        'data':data,
        'cat_count':cat_count,
        'product_count':product_count,
        'user_count':user_count,
        'p_date':p_date,
        'p_day':p_day,
        'c_date':c_date,
        'c_day':c_day,
        'u_date':u_date,
        'u_day':u_day
    }
    return render(request,'admin/dashboard.html',context)

#admin register
def register(request):
    if request.method == 'POST':
            first_name=request.POST['first_name']
            last_name=request.POST['last_name']
            username=request.POST['username']
            password1=request.POST['password1']
            password2=request.POST['password2']
            email=request.POST['email']
            phonenumber=request.POST['phonenumber']
            if password1==password2:
                if Account.objects.filter(username=username).exists():
                    messages.error(request,'Username Taken')
                    return redirect('register')
                elif Account.objects.filter(email=email).exists():
                    messages.error(request,'Email already taken')
                    return redirect('register')
                else:
                    user=Account.objects.create_user(username=username,password=password1,email=email,first_name=first_name,last_name=last_name,phonenumber=phonenumber)
                    user.save()
                   
                    print('user created')
                    return redirect('user_login')
            else:
                messages.error(request,'password not matching..')
                return redirect('register')
    else:
        return render(request,'register.html')

#admin view product page
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def product(request):
    products=Product.objects.all().filter(is_available=True).order_by('-created_date')
    paginator=Paginator(products,3)
    page=request.GET.get('page')
    paged_products=paginator.get_page(page)
    product_count=products.count()
    try:
        page_objects = paginator.page(page)
    except PageNotAnInteger:
        page_objects = paginator.page(1)
    except EmptyPage:
        page_objects = paginator.page(paginator.num_pages)    
    context={
        'products':paged_products,
        'product_count':product_count,
        'page_objects' : page_objects,
       
    }
    #products = Product.objects.all().order_by('-created_date')
    return render(request,'admin/product.html',context)

#admin add product
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def addProduct(request):
    if request.method=='POST':
        form=ProductForm(request.POST,request.FILES)
        if form.is_valid():
            product=form.save(commit=False)
            product.is_available=True
            if product.offer is not None:
                product.price=product.actual_price - ( (product.actual_price * product.offer) / 100)
            else:
                product.price=product.actual_price
            form.save()
            return redirect('product')
        else:
            return redirect('addProduct')
    else:
        form=ProductForm()
        context={'form':form}
        return render(request,'admin/addProduct.html',context)

#admin delete product
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def deleteproduct(request,id):
    Product.objects.filter(id=id).delete()
    return redirect('product')

#admin edit product
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def editproduct(request,id):
    product=Product.objects.get(id=id)
    if request.method == 'POST':
        form=ProductForm(request.POST,request.FILES,instance=product)
        if form.is_valid():
            product=form.save(commit=False)
            product.is_available=True
            if product.offer is not None:
                product.price=product.actual_price - ( (product.actual_price * product.offer) / 100)
            else:
                product.price=product.actual_price
            form.save()
            return redirect('product')
    else:
        form=ProductForm(instance=product)
        return render(request,'admin/editproduct.html',{'product':product,'form':form})

#search a product
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def search_product(request):
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            products=Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count=products.count()
        else:
            return redirect('product')
    context={
        'products':products,
        'product_count':product_count
    }
    return render(request,'admin/product.html',context)

#admin add category
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def addCategory(request): 
    if request.method=='POST': 
        form=CategoryForm(request.POST,request.FILES)
        if form.is_valid():
            print('working')
            form.save()
            return redirect('category')
        else:
            messages.info(request,'Category Already Exists')
            return redirect('addCategory')
    else:
        form=CategoryForm()
        context={'form':form}
        return render(request,'admin/addCategory.html',context)

#admin view all category
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def category(request):
    categories = Category.objects.all()
    return render(request,'admin/category.html',{'categories':categories})

#admin delete category
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def deletecategory(request,id):
    print("DELETE")
    Category.objects.filter(id=id).delete()
    return redirect('category')

#admin delete category
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def editcategory(request,id):
    category=Category.objects.get(id=id)
    if request.method == 'POST':
        form=CategoryForm(request.POST,request.FILES,instance=category)
        if form.is_valid():
            form.save()
            return redirect('category')
    else:
        form=CategoryForm(instance=category)
        return render(request,'admin/editcategory.html',{'category':category,'form':form})

#search a category
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def search_category(request):
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            categories=Category.objects.order_by('-created_date').filter(Q(category_name__icontains=keyword) | Q(description__icontains=keyword))
            category_count=categories.count()
    context={
        'categories':categories,
        'category_count':category_count
    }
    return render(request,'admin/category.html',context)

#view all users
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def user_manage(request):
    users=Account.objects.all().order_by('-date_joined')
    paginator=Paginator( users,3)
    page=request.GET.get('page')
    paged_users=paginator.get_page(page)
    user_count=users.count()
    try:
        page_objects = paginator.page(page)
    except PageNotAnInteger:
        page_objects = paginator.page(1)
    except EmptyPage:
        page_objects = paginator.page(paginator.num_pages)    
    context={
        'users':paged_users,
        'user_count': user_count,
        'page_objects' : page_objects,

    }
    return render(request,'admin/user_manage.html',context)
def deleteuser(request,id):
    Account.objects.filter(id=id).delete()
    return redirect('user_manage')
#block user
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def blockuser(request,id):
    user=Account.objects.get(id=id)
    user.is_active=False
    user.save()
    return redirect('user_manage')

#unblock user
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def unblockuser(request,id):
    user=Account.objects.get(id=id)
    user.is_active=True
    user.save()
    return redirect('user_manage')

#search a user
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def search_user(request):
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            users=Account.objects.order_by('-date_joined').filter(Q(first_name__icontains=keyword) | Q(username__icontains=keyword))
           
    context={
        'users':users,
        
    }
    return render(request,'admin/user_manage.html',context)


#view product variations
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def variation(request):
    variations=Variation.objects.all().order_by('-created_date')
    paginator=Paginator( variations,3)
    page=request.GET.get('page')
    paged_variations=paginator.get_page(page)
 
    try:
        page_objects = paginator.page(page)
    except PageNotAnInteger:
        page_objects = paginator.page(1)
    except EmptyPage:
        page_objects = paginator.page(paginator.num_pages)    
    context={
        'variations':paged_variations,
        'page_objects' : page_objects,

    }
   
    return render(request,'admin/variation.html',context)

#search a product
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def search_variation(request):
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            variations=Variation.objects.order_by('-created_date').filter(Q(variation_value__icontains=keyword) | Q(variation_category__icontains=keyword))
           
    context={
        'variations':variations,
    
    }
    return render(request,'admin/variation.html',context)

#edit variations
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def editvariation(request,id):
    variation=Variation.objects.get(id=id)
    if request.method == 'POST':
        form=VariationForm(request.POST,request.FILES,instance=variation)
        if form.is_valid():
            form.save()
            return redirect('variation')
    else:
        form=VariationForm(instance=variation)
        return render(request,'admin/editvariation.html',{'variation':variation,'form':form})

#delete product variation
def delete_variation(request,id):
    Variation.objects.filter(id=id).delete()
    return redirect('variation')

#add variation
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def addvariation(request): 
    if request.method=='POST': 
        form=VariationForm(request.POST,request.FILES)
        if form.is_valid():
            print('working')
            form.save()
            return redirect('variation')
        else:
            messages.info(request,'Variation Already Exists')
            return redirect('addvariation')
    else:
        form=VariationForm()
        context={'form':form}
        return render(request,'admin/addvariation.html',context)

#view all orders of users
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def orderManage(request):
    orderproducts=OrderProduct.objects.all().order_by('-created_at')
    paginator=Paginator( orderproducts,6)
    page=request.GET.get('page')
    paged_orders=paginator.get_page(page)
    order_count=orderproducts.count()
    try:
        page_objects = paginator.page(page)
    except PageNotAnInteger:
        page_objects = paginator.page(1)
    except EmptyPage:
        page_objects = paginator.page(paginator.num_pages)    
    context={
        'orderproducts':paged_orders,
        'order_count': order_count,
        'page_objects' : page_objects,

    }
    return render(request,'admin/orderManage.html',context)

#order status
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def status(request,id):
    status=request.POST['status']
    print(status)
    orderstatus=OrderProduct.objects.filter(id=id).update(status=status)
    return redirect('orderManage')

#add category from add product page
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def addCategoryProduct(request): 
    if request.method=='POST': 
        form=CategoryForm(request.POST,request.FILES)
        if form.is_valid():
            print('working')
            form.save()
            return redirect('addProduct')
        else:
            messages.info(request,'Category Already Exists')
            return redirect('addCategory')
    else:
        form=CategoryForm()
        context={'form':form}
        return render(request,'admin/addCategory.html',context)

#sales report
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def sales_report(request,total=0, quantity=0, cart_items=None):
    if request.method == 'POST':
          date_from=request.POST['datefrom']
          date_to=request.POST['dateto']
          order_search=OrderProduct.objects.filter(created_at__range=[date_from,date_to])
          return render(request,'admin/sales_report.html',{'orders':order_search})
    else:
        users = Account.objects.all()
        orders = OrderProduct.objects.all()
        return render(request, "admin/sales_report.html",{'orders':orders,'users':users})


        
        
#search sales
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def search_sales(request):
    if 'keyword' in request.GET:
        keyword=request.GET['keyword']
        if keyword:
            orders=OrderProduct.objects.order_by('-created_at').filter(Q(status__icontains=keyword) | Q(product_price__icontains=keyword))
           
    context={
        'orders':orders,
        
    }
    return render(request,'admin/sales_report.html',context)

#export to csv file
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def export_csv(request):
    response=HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename=Order'+\
        str(datetime.datetime.now())+'.csv'
    writer=csv.writer(response)
    writer.writerow(['id','created_at','quantity','status','product_price'])
    orders=OrderProduct.objects.filter(ordered=True).order_by('-created_at')
    for order in orders:
        writer.writerow([order.id,order.created_at,order.quantity,order.status,order.product_price])
    return response

# export to excel file
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename = OrderProduct ' + \
        str(datetime.datetime.now()) + '.xls'

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('OrderProduct')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['id','created_at','quantity','status','product_price']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = OrderProduct.objects.filter(ordered=True).order_by('-created_at').values_list(
        'id','created_at','quantity','status','product_price')

    for row in rows:
        row_num += 1

        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)

    wb.save(response)

    return response

# export to pdf file
@login_required(login_url='login')
@user_passes_test(lambda user: user.is_superadmin,login_url='login')
def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename = OrderProduct ' + \
        str(datetime.datetime.now()) + '.pdf'
    response['Content-Transfer-Encoding'] = 'binary'

    orders = OrderProduct.objects.filter(ordered=True).order_by('-created_at')

    html_string = render_to_string('admin/pdf_output.html', {
                                   'orders': orders, 'total': 0})
    html = HTML(string=html_string)

    result = html.write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output = open(output.name, 'rb')
        response.write(output.read())

    return response

def offer_manage(request):
    pass