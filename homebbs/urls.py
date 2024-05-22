from django.urls import path
from.import views



app_name = 'homebbs'
urlpatterns = [
    path('', views.homepage, name='home'),
    path('shop/',views.shoppage,name='shop'),
    path('itempage/<int:product_id>/',views.itempage,name='item'),
    path('addcart/<int:pk>/',views.addtocart,name='addcart'),
    path('cart/',views.cartpage,name='cart'),
    path('checkout/',views.checkoutpage,name='checkout'),
    path('wishlist/',views.wishlist,name='wishlist'),
    path('addwishlist/<int:pk>/',views.addwishlist,name='addwishlist'),
    path('removefromwishlist/<int:pk>/',views.removefromwishlist,name='wishlistremove'),
    path('wishaddcart/<int:pk>/',views.wishaddcart,name='wishaddcart'),
    path('checkaddress/',views.checkaddress,name='checkaddress'),
    path('profile/',views.userprofile,name='profile'),
    path('editprofile/',views.editprofile,name='editprofile'),
    path('decrement/<int:id>/',views.decrement_count,name='decrement'),
    path('increment/<int:id>/',views.increment_count,name='increment'),
    path('remove/<int:id>/',views.removefromcart,name='remove'),
    path('addaddress/',views.address,name='addaddress'),    
    path('editaddress/<int:add_id>/',views.editaddress,name='editaddress'),
    path('addremove/<int:add_id>/',views.addressremove,name='addremove'),
    path('error/',views.errorpage,name='error'),
    path('orderconfirm/',views.order_confirm,name='orderconfirm'),
    path('changepassword/',views.changepassword,name='changepassword'),
    path('orderlist/',views.orderlist,name='orderlist'),
    path('orderdetails/<int:order_id>/',views.orderdetails,name='orderdetails'),
    path('cancelorder/<int:order_id>/',views.cancelorder,name='cancelorder'),
    path('returnorder/<int:order_id>/',views.returnorder,name='returnorder'),
    path('wallet/',views.wallet,name='wallet'),
    path('wallethistory/',views.wallethistory,name='wallethistory'),
    path('generate_invoice/<int:order_id>/',views.generate_invoice,name='generate_invoice'),
    path('gallery/',views.gallery,name='gallery'),
    path('razor_success/', views.razor_success, name="razor_success"),








    # path('addtocatshop/<int:prod_id>/',views.addtocartshop,name='addtocartshop'),










]