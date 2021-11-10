
from django.urls import path
from . import views
urlpatterns = [
  
    path('',views.login,name='login'),
    path('login',views.login,name='login'),
    path('logincheck',views.logincheck,name='logincheck'),
    path('adminlogout',views.adminlogout,name='adminlogout'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('product/',views.product,name='product'),
    path('addProduct/',views.addProduct,name='addProduct'),
    path('addCategory/',views.addCategory,name='addCategory'),
    path('category/',views.category,name='category'),
    path('deleteproduct/<id>/',views.deleteproduct,name='deleteproduct'),
    path('deletecategory/<id>',views.deletecategory,name='deletecategory'),
    path('editproduct/<id>',views.editproduct,name='editproduct'),
    path('editcategory/<id>',views.editcategory,name='editcategory'),
    path('user_manage',views.user_manage,name='user_manage'),
    path('blockuser/<id>',views.blockuser,name='blockuser'),
    path('unblockuser/<id>',views.unblockuser,name='unblockuser'),
    path('variation/',views.variation,name='variation'),
    path('editvariation/<id>',views.editvariation,name='editvariation'),
    path('addvariation/',views.addvariation,name='addvariation'),
    path('orderManage/',views.orderManage,name='orderManage'),
    path('status/<id>',views.status,name='status'),
    path('addCategoryProduct/',views.addCategoryProduct,name='addCategoryProduct'),
    path('deleteuser/<id>/',views.deleteuser,name='deleteuser'),
    path('search_product',views.search_product,name='search_product'),
    path('sales_report/',views.sales_report,name='sales_report'),
    path('export_csv/',views.export_csv,name='export_csv'),
    path('export_excel/',views.export_excel,name='export_excel'),
    path('export_pdf/',views.export_pdf,name='export_pdf'),
    path('search_category/',views.search_category,name='search_category'),
    path('search_user',views.search_user,name='search_user'),
    path('search_variation/',views.search_variation,name='search_variation'),
    path('search_sales',views.search_sales,name='search_sales'),
    path('offer_manage',views.offer_manage,name='offer_manage'),
    path('delete_variation/<id>/',views.delete_variation,name='delete_variation')
]


