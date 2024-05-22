from django.shortcuts import render,redirect, get_object_or_404
from registrationebbs.models import Custom_User
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from adminebbs.models import Category,Product,Image,Coupons
from homebbs.models import Cart,Address,Order,Orderaddress,Wishlist,Mywallet,Wallethistory,Razorpayuser
from datetime import date, timedelta
from decimal import Decimal
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.db.models import Q,F
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse,HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import get_template
from xhtml2pdf import pisa
import razorpay
import uuid
from uuid import uuid4


def homepage(request):
    return render(request,'home.html')

def gallery(request):
    return render(request,'gallery.html')


def errorpage(request):
    return render(request,'error.html')


def shoppage(request):
    if request.user.is_authenticated:
        if not request.user.is_active:
            return redirect('r:login')
        else:
            pass
        categories = Category.objects.all()
        selected_category = None
        products = Product.objects.all()
        sort_by = request.GET.get('sort')
        category_id = request.GET.get('category')

        if category_id:
            try:
                selected_category = Category.objects.get(id=category_id)
                products = products.filter(category=selected_category)
            except Category.DoesNotExist:
                pass
                
        if sort_by:
            if sort_by == 'price_low_to_high':
                products = products.order_by('price')
            elif sort_by == 'price_high_to_low':
                products = products.order_by(F('price').desc())


        if request.method == 'POST':
            search = request.POST.get('search')
            if search:
                products = products.filter(Q(name__icontains=search) | Q(description__icontains=search)) 

        paginator = Paginator(products,4)
        page_number = request.GET.get('page')
        try:
            products = paginator.page(page_number)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

        return render(request, 'shop.html', {'products': products, 'categories': categories, 'selected_category': selected_category})
    
    return redirect('r:login')


# def addtocartshop(request,prod_id):
#     if request.user.is_authenticated:
#         current_user = request.user
#         product = Product.objects.get(id=prod_id)
#         use = Custom_User.objects.get(user=current_user)
#         try:
#             cart_item = Cart.objects.get(user=use,product=product)
#             cart_item.quantity += 1
#         except Cart.DoesNotExist:
#             cart_item = Cart.objects.create(
#                 user = use,
#                 product = product,
#                 quantity = 1
#             )
#         cart_item.save()
#         return redirect('u:shop')




@login_required
def itempage(request,product_id):
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.all()
        if not request.user.is_active:
            return redirect('r:login')
        else:
            pass
        obj = Product.objects.get(id = product_id)
        return render(request,'itempage.html',{'product':obj})
    return redirect('r:login')



@login_required
def addtocart(request,pk):
    if request.user.is_authenticated:
        obj = Product.objects.get(id=pk)
        use = Custom_User.objects.get(user_id = request.user.id)

        try:
            cart_items = Cart.objects.get(user=use, product=obj)
            if cart_items.quantity < cart_items.product.stock:
                cart_items.quantity += 1
                cart_items.save()
            return redirect('u:cart')
        except Cart.DoesNotExist:
            items = Cart.objects.create(
                product=obj,
                user = use
                )
            items.save()     
            return redirect('u:cart')

        return render(request,'cart.html')
    return redirect('r:login')



def cartpage(request):
    if request.user.is_authenticated:
        user = Custom_User.objects.get(user_id = request.user.id)
        obj = Cart.objects.filter(user = user)
        address = Address.objects.filter(user_id = user.id)
        address2 = address.first()
        total = 0
        for i in obj:
            total += (i.product.discount_price * i.quantity)
        checkout = True
        request.session['checkout'] = checkout
        subtotal = total
        return render(request,'cart.html',{'cart':obj,'total':total,'subtotal':subtotal ,'address':address2})
    return redirect('r:login')



@login_required
def checkoutpage(request):
    if request.user.is_authenticated:
        checkout = request.session.get('checkout')
        if checkout:
            user = Custom_User.objects.get(user_id = request.user.id)
            obj = Cart.objects.filter(user = user)
            quantity = 0
            order = None
            discount = 0
            payment = None
            tot = 0
            prod_name = []
            for cart_items in obj:
                quantity += cart_items.quantity
                tot+=cart_items.product.discount_price * cart_items.quantity
                prod_name.append(cart_items.product.name)

            user_wallet = Mywallet.objects.get_or_create(user=user)[0]
            wallet_amount = user_wallet.amount

            client = razorpay.Client(auth = (settings.RAZORPAY_KEY,settings.RAZORPAY_SECRET))
            payment = client.order.create({'amount':tot * 100,'currency':'INR','payment_capture':1})
           
            if request.method == 'POST':
                if 'couponcode' in request.POST:
                    coup_id = request.POST.get('couponcode')
                    coupon = Coupons.objects.get(code=coup_id) 
                    if coupon.count > 0 :
                        discount = coupon.discount_price
                        request.session['applied_coupon'] = coup_id
                        messages.error(request, f"Coupon applied successfully!")
                    else:
                        messages.error(request, f"Apologies, this coupon is no longer valid.")
                        return redirect('u:checkout')
                   
                    # 2nd form for address
                elif 'address' in request.POST:
                    add_id = request.POST.get('address')
                    payment_type = request.POST.get('payment')
                    address = Orderaddress.objects.get(id=add_id)
                    subtotal = Decimal(request.POST.get('total'))
                    disc = Decimal(request.POST.get('discount'))
                    sub_total = subtotal - disc

                    request.session['selected_address'] = add_id
                    request.session['payment_type'] = payment_type
                        
                    if payment_type == 'wallet':
                        user_wallet = Mywallet.objects.get_or_create(user=user)[0]
                        if user_wallet.amount >= tot:
                            user_wallet.amount -= tot
                            user_wallet.save()

                            wallet_history = Wallethistory.objects.create(
                                amount=tot,
                                transaction_type='Debited',
                                category = 'Amount debited',
                                user=user
                            )
                            wallet_history.save()
                        else:
                            messages.error(request, "Insufficient balance in your wallet.")
                            return redirect('u:checkout')

                    if payment_type == 'Cash On Delivery' and sub_total > 1000:
                        messages.error(request, "Sorry COD is not allowed for orders exceeding 1000 Rs")
                        return redirect('u:checkout')

                    order_id = str(uuid4())[:4] 
                    current_time = timezone.now().time()
                    order = Order.objects.create(
                        total_orderprice = sub_total,
                        order_id=order_id,
                        price = subtotal,
                        date = date.today(),
                        time = current_time,
                        status = 'Ordered',
                        payment_type = payment_type,
                        quantity = quantity,
                        discount = disc,
                        user = user,
                        orderaddress = address,
                    )
                    if payment == 'online':
                        razor = request.session.get('razor_id')
                        razo = Razorpayuser.objects.get(id = razor)
                        razo.order = order
                        razo.save()
                                            

                    if 'applied_coupon' in request.session:
                        coup_id = request.session['applied_coupon']
                        coupon = Coupons.objects.get(code=coup_id)
                        coupon.count -= 1
                        coupon.save()

                    for cart_item in obj:
                        if cart_item.product.stock < cart_item.quantity:
                            messages.error(request, f"Apologies, stock limit exceeded")
                            return redirect('u:checkout')
                        product = cart_item.product
                        product.stock -= cart_item.quantity
                        product.save()
                        order.product.add(product)
                    obj.delete()
                    for items in obj:
                        order.product.add(items.product)
                    return redirect('u:orderconfirm')

            user = Custom_User.objects.get(user_id = request.user.id)
            obj = Cart.objects.filter(user = user)
            address = Orderaddress.objects.filter(user_id = user.id)
            total = 0
            for i in obj:
                total += (i.product.discount_price * i.quantity)
            ordered = True
            request.session['ordered'] = ordered      
            cart_total_price = 0
            total_amount = total * 100

            applied_coupon = request.session.get('applied_coupon')
            selected_address = request.session.get('selected_address')
            payment_type = request.session.get('payment_type')
            error_messages = [str(message) for message in messages.get_messages(request)]

            return render(request,'checkout.html',{'cart':obj,'orderaddress':address,'total':total,'discount':discount,'payment':payment,'applied_coupon':applied_coupon,'selected_address':selected_address,'total_amount':total_amount,'wallet_amount':wallet_amount,'error_messages':error_messages})
        return redirect('u:shop')
    return redirect('r:login')
  


def checkaddress(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            name = request.POST.get('name')
            phone_no = request.POST.get('phoneno')
            house_no = request.POST.get('houseno')
            street = request.POST.get('street')
            city = request.POST.get('city')
            landmark = request.POST.get('landmark')
            pincode = request.POST.get('pincode')
            user_id =  Custom_User.objects.get(user = request.user.id)

            if user_id is not None:
                address = Orderaddress.objects.create(
                    name=name,
                    phoneno=phone_no,
                    houseno=house_no,
                    street=street,
                    city=city,
                    landmark=landmark,
                    pincode=pincode,
                    user=user_id,
                )
                address.save()
                redirect_url = reverse('u:checkout')
                return redirect(redirect_url)
            else:
                pass
        return render(request,'checkaddress.html')
    return redirect('r:login')



def wishlist(request):
    if request.user.is_authenticated:
        userr = Custom_User.objects.get(user=request.user)
        wishlist = Wishlist.objects.filter(user = userr)
        return render(request, 'wishlist.html',{'wishlist':wishlist})
    return redirect('r:login')


def addwishlist(request,pk):
    if request.user.is_authenticated:
        prod = Product.objects.get(id=pk)
        userr = Custom_User.objects.get(user_id= request.user.id)

        if Wishlist.objects.filter(user=userr,product=prod).exists():
            return JsonResponse({'exists':True})

        else:
            items = Wishlist.objects.create(
                product = prod,
                user = userr
                )
            items.save()
            return JsonResponse({'added':True})
    return redirect('r:login')


def removefromwishlist(request,pk):
    obj = Wishlist.objects.get(id=pk)
    obj.delete()
    return redirect('u:wishlist')
        


def wishaddcart(request,pk):
    if request.user.is_authenticated:
        prod = Product.objects.get(id=pk)
        userr = Custom_User.objects.get(user_id=request.user.id) 
        if Cart.objects.filter(user=userr,product=prod).exists():
            return JsonResponse({'exists':True})
        else:
            cart_items = Cart.objects.create(
                product = prod,
                user = userr
                )
            cart_items.save()
            Wishlist.objects.filter(user=userr,product=prod).delete()
            return JsonResponse({'added':True})
        return redirect('u:wishlist')
    return redirect('r:login')




def order_confirm(request):
    if request.user.is_authenticated:
        ordered = request.session.get('ordered')
        checkout = request.session.get('checkout')
        if ordered:
            del request.session['ordered']
            del request.session['checkout']
            return render(request,'order_confirm.html')
        return redirect('u:shop')
    return redirect('r:login')


@login_required
def orderlist(request):
    if request.user.is_authenticated:
        for key, value in request.GET.items():
            print(f"Parameter: {key}, Value: {value}")

        userr = Custom_User.objects.get(user=request.user)
        orders = Order.objects.filter(user = userr).order_by('-id')

        paginator = Paginator(orders,4)
        page = request.GET.get('page')
        try:
            orders = paginator.page(page)
        except PageNotAnInteger:
            orders = paginator.page(1)
        except EmptyPage:
            orders = paginator.page(paginator.num_pages)

        for order in orders:
            order.delivery_date_plus_7_days = order.date + timedelta(days=7)
        try:
            url = reverse('orderlist')
            url+=f'?page={value}'
            return render(request,url,{'orders':orders})
        except:
            return render(request,'orderlist.html',{'orders':orders})
    return redirect('r:login')



def cancelorder(request, order_id):
    order = Order.objects.get(id=order_id)
    user = Custom_User.objects.get(user_id=request.user.id)
    order.status = 'Cancelled'
    order.save()
    if order.payment_type == 'Cash On Delivery':
        return redirect('u:orderlist')
    try:
        wallet = Mywallet.objects.get(user=user)
    except Mywallet.DoesNotExist:
        wallet_amount = order.total_orderprice
        wallet_payment_type = order.payment_type
        wall = Mywallet.objects.create(
            user=user,
            amount=wallet_amount,
            payment_type=wallet_payment_type
        )
        wall.save()
        history = Wallethistory.objects.create(
            user=user,
            amount=order.price,
            transaction_type = 'Credited',
            category = 'From Cancelled Order'
        )
        history.save()
        return redirect('u:orderlist')
    else:
        wallet.amount += order.total_orderprice
        wallet.save()
        history = Wallethistory.objects.create(
            user=user,
            amount=order.price,
            transaction_type = 'Credited',
            category = 'From Cancelled Order'
        )
        history.save()  
    return redirect('u:orderlist')



def generate_invoice(request,order_id):
    template_path = 'invoice.html'
    try:
        order = Order.objects.get(id=order_id)
        user = Custom_User.objects.get(user_id=request.user.id)
    except Order.DoesNotExist:
        return HttpResponse("Order does not exist")
    products = order.product.all()
    context = {'order':order,'user':user,'products': products}

    if order.orderaddress:
        context['order_address'] = order.orderaddress

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    template = get_template(template_path)
    html = template.render(context)


    pisa_status = pisa.CreatePDF(
       html, dest=response ,encoding='UTF-8')
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



def returnorder(request,order_id):
    order = Order.objects.get(id=order_id)
    user = Custom_User.objects.get(user_id=request.user.id)
    order.status = 'Return Initiated'
    order.save()

    for key, value in request.GET.items():
        print(f"Parameter: {key}, Value: {value}")

    try:
        wallet = Mywallet.objects.get(user=user)
    except Mywallet.DoesNotExist:
        wallet_amount = order.total_orderprice
        wallet_payment_type = order.payment_type
        wall = Mywallet.objects.create(
            user=user,
            amount=wallet_amount,
            payment_type=wallet_payment_type
        )
        wall.save()
        history = Wallethistory.objects.create(
            user=user,
            amount=order.price,
            transaction_type = 'Credited',
            category = 'From returned Order'
        )
        history.save()
        return redirect('u:orderlist')
    else:
        wallet.amount += order.total_orderprice
        wallet.save()
        history = Wallethistory.objects.create(
            user=user,
            amount=order.price,
            transaction_type = 'Credited',
            category = 'From returned Order'

        )
        history.save()  
    return redirect('u:orderlist')



def orderdetails(request,order_id):
    if request.user.is_authenticated:
        order = Order.objects.get(id=order_id)
        return render(request,'orderdetails.html',{'order':order})
    return redirect('r:login')



def removefromcart(request,id):
    obj = Cart.objects.get(id=id)
    obj.delete()
    return redirect('u:cart')


def increment_count(request, id):
    obj = Cart.objects.get(id=id)
    if obj.product.stock > obj.quantity:
        obj.quantity += 1
        obj.save()
        total = 0
        userr = Custom_User.objects.get(user = request.user)
        for cart in Cart.objects.filter(user=userr):
            total += cart.product.discount_price*cart.quantity
        updated_total = total + 10
        return JsonResponse({'quantity': obj.quantity,'total':total,'updatedTotal': updated_total})
    else:
        return JsonResponse({'error': 'Maximum stock reached'})


def decrement_count(request, id):
    obj = Cart.objects.get(id=id)
    if obj.quantity > 1:
        obj.quantity -= 1
        obj.save()
        quant = 0
        total = 0
        userr = Custom_User.objects.get(user = request.user)
        for cart in Cart.objects.filter(user=userr):
            total += cart.product.discount_price*cart.quantity
            quant += cart.quantity
        updated_total = total + 10
        return JsonResponse({'quantity': obj.quantity,'total':total,'updatedTotal': updated_total })
    else:
        return JsonResponse({'error': 'Minimum quantity reached'})


def userprofile(request):
    if request.user.is_authenticated:
        custom_user = Custom_User.objects.get(user=request.user)
        addresses = custom_user.user_address.all()
        address = Address.objects.filter(user_id = custom_user)
        return render(request,'userprofile.html',{'custom_user':custom_user,'addresses': addresses})
    return redirect('r:login')


@login_required
def editprofile(request):
    if request.user.is_authenticated:
        try:
            obj = Custom_User.objects.get(user = request.user)
        except Adress.DoesNotExist:
            return redirect('u:profile')

        if request.method == 'POST':
            obj.name = request.POST.get('name',obj.name)
            obj.email = request.POST.get('email',obj.email)
            obj.phone_number = request.POST.get('phone_number',obj.phone_number)
            obj.gender = request.POST.get('gender',obj.gender)
            obj.age = request.POST.get('age',obj.age)
            obj.save()
            return redirect('u:profile')
        return render(request,'usereditprof.html',{'userr':obj})
    return redirect('r:login')

@login_required
def address(request):
    if request.user.is_authenticated:

        if request.method == 'POST':
            name = request.POST.get('name')
            phone_no = request.POST.get('phoneno')
            house_no = request.POST.get('houseno')
            street = request.POST.get('street')
            city = request.POST.get('city')
            landmark = request.POST.get('landmark')
            pincode = request.POST.get('pincode')
            user_id =  Custom_User.objects.get(user = request.user.id)

            if user_id is not None:
                address = Address.objects.create(
                    name=name,
                    phoneno=phone_no,
                    houseno=house_no,
                    street=street,
                    city=city,
                    landmark=landmark,
                    pincode=pincode,
                    user=user_id,
                )
                address.save()
                return redirect('u:profile')
            else:
                pass
        return render(request,'addaddress.html')
    return redirect('r:login')


@login_required
def editaddress(request,add_id):
    if request.user.is_authenticated:
        custom_user = Custom_User.objects.get(user=request.user)
        obj = Address.objects.get(id=add_id,user = custom_user)
        if request.method == 'POST':
            obj.houseno = request.POST.get('houseno')
            obj.street = request.POST.get('street')
            obj.city = request.POST.get('city')
            obj.landmark = request.POST.get('landmark')
            obj.pincode = request.POST.get('pincode')
            obj.save()
            return redirect('u:profile')
        return render(request,'addressedit.html',{'adder':obj})
    return redirect('r:login')


@login_required
def addressremove(request,add_id):
    obj = Address.objects.get(id=add_id)
    obj.delete()
    return redirect('u:profile')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def changepassword(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            current_password =  request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if check_password(current_password,request.user.password):
                if new_password == confirm_password:
                    request.user.set_password(new_password)
                    request.user.save()
                    update_session_auth_hash(request,request.user)
                    # logout(request)
                    return redirect('u:profile')
                err = 'Password must be same'
                return render(request,'changepass.html',{'err':err})
            err2 = 'Current password is wrong'
            return render(request,'changepass.html',{'err2':err2})
        return render(request,'changepass.html')
    return redirect('r:login')



def wallet(request):
    if request.user.is_authenticated:
        user = Custom_User.objects.get(user_id=request.user.id)
        wallet , created = Mywallet.objects.get_or_create(user=user)
        return render(request,'wallet.html',{'wallet':wallet})
    return redirect('r:login')


def wallethistory(request):
    if request.user.is_authenticated:
        history = Wallethistory.objects.all()
        return render(request,'wallethistory.html',{'history':history})
    return redirect('r:login')

@csrf_exempt
def razor_success(request):
    if request.method == 'POST':
        print('some')
        print(request.POST)
        razorpay_payment_id = request.POST.get('payment_id')
        razorpay_order_id = request.POST.get('order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        print(razorpay_payment_id)

        razorpayment = Razorpayuser.objects.create(
            razorpay_orderid = razorpay_order_id,
            razorpay_paymentid = razorpay_payment_id, 
        )
        razorpayment.save()

        request.session['razor_id'] = razorpayment.id

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

