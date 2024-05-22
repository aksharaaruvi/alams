from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from.import views


app_name = 'adminebbs'
urlpatterns = [
    path('dashboard/',views.admindash,name='dashboard'),
    path('adminuser/', views.adminuser, name='adminuser'),
    path('adminuserblock/<int:user_id>/',views.user_block,name='user_block'),
    path('adminuserunblock/<int:user_id>/',views.user_unblock,name='user_unblock'),
    path('admincategory/',views.admincategory,name='categorymanagement'),
    path('addcategory/',views.addcategory,name='addcategory'),
    path('editcategory/',views.editcategory,name='editcategory'),
    path('listunlist/',views.categorylist,name='listunlist'),
    path('unlistlist/',views.productlist,name='unlistlist'),
    path('adminproduct/',views.adminproduct,name='productmanagement'),
    path('productedit/<int:product_id>/',views.editproduct,name='editproduct'),
    path('productadd/',views.addproduct,name='addproduct'),
    path('removeimage/<int:image_id>/',views.removeimage,name='removeimage'),
    path('adminorder/',views.adminorder,name='adminorder'),
    path('adminorderdetails/<int:order_id>/',views.adminorderdetails,name='adminorderdetails'),
    path('orderstatus/<int:order_id>/', views.orderstatus, name='orderstatus'),
    path('admincoupon/', views.admincoupon, name='admincoupon'),
    path('couponadd/', views.couponadd, name='couponadd'),
    path('couponedit/<int:coupon_id>/', views.couponedit, name='couponedit'),
    path('couponremove/<int:coupon_id>/', views.couponremove, name='couponremove'),
    path('get_coupons/', views.get_coupons, name='get_coupons'),
    path('salesreport/', views.salesreport, name='salesreport'),
    path('generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('generate_excel/', views.generate_excel, name='generate_excel'),
    path('addoffer/',views.addoffer,name='addoffer')














    

     

] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)