from django.shortcuts import render,redirect
from registrationebbs.models import Custom_User
from adminebbs.models import Category,Product,Image,Coupons
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse
from homebbs.models import Address,Order
from datetime import datetime, timedelta, date
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import JsonResponse,HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import json
from django.db.models import Sum, Count
from django.views.decorators.cache import cache_control
import openpyxl
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admindash(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            overall_sales_count = Order.objects.count()
            overall_order_amount_result = Order.objects.aggregate(total_amount=Sum('price'))
            overall_order_amount = overall_order_amount_result['total_amount'] if overall_order_amount_result['total_amount'] else 0
            overall_discount_count = Coupons.objects.aggregate(total_count=Count('id'))['total_count'] or 0

            best_selling_product = Order.objects.values('product__name').annotate(total_quantity=Count('product')).order_by('-total_quantity').first()
            best_selling_product_name = best_selling_product['product__name'] if best_selling_product else None

            best_selling_category = Product.objects.values('category__name').annotate(total_quantity=Count('orderproduct__quantity')).order_by('-total_quantity').first()
            best_selling_category_name = best_selling_category['category__name'] if best_selling_category else None

            today = date.today()
            year = today.year
            month = today.month     

            today_orders = Order.objects.filter(date=today, status__in=['Ordered', 'Delivered']).values('product__name').annotate(count=Count('id'))
            today_canceled_and_returned_orders = Order.objects.filter(date=today, status__in=['Cancelled', 'Returned']).values('product__name').annotate(count=Count('id'))

            monthly_orders = Order.objects.filter(date__year=year, date__month=month, status__in=['Ordered', 'Delivered']).values('product__name').annotate(count=Count('id'))
            monthly_canceled_orders = Order.objects.filter(date__year=year, date__month=month, status__in=['Cancelled', 'Returned']).values('product__name').annotate(count=Count('id'))

            yearly_orders = Order.objects.filter(date__year=year, status__in=['Ordered', 'Delivered']).values('product__name').annotate(count=Count('id'))
            yearly_canceled_orders = Order.objects.filter(date__year=year, status__in=['Cancelled', 'Returned']).values('product__name').annotate(count=Count('id'))


            order_data = {}
            for order in today_orders:
                product_name = order['product__name']
                order_data.setdefault(product_name, {'ordered': 0, 'canceled': 0})
                order_data[product_name]['ordered'] += order['count']

            for canceled_and_returned_order in today_canceled_and_returned_orders:
                print(canceled_and_returned_order)
                product_name = canceled_and_returned_order['product__name']
                order_data.setdefault(product_name, {'ordered': 0, 'canceled': 0})
                order_data[product_name]['canceled'] += canceled_and_returned_order['count']


            monthly_order_data = {}
            monthly_canceled_data = {}
            for order in monthly_orders:
                monthly_order_data[order['product__name']] = order['count']

            for canceled_order in monthly_canceled_orders:
                monthly_canceled_data[canceled_order['product__name']] = canceled_order['count']

            yearly_order_data = {}
            yearly_canceled_data = {}
            for order in yearly_orders:
                yearly_order_data[order['product__name']] = order['count']

            for canceled_order in yearly_canceled_orders:
                yearly_canceled_data[canceled_order['product__name']] = canceled_order['count']


            return render (request,'dashboard.html',{'overall_sales_count':overall_sales_count,'overall_order_amount':overall_order_amount,'overall_discount_count':overall_discount_count,'best_selling_product_name':best_selling_product_name,'best_selling_category_name':best_selling_category_name,'order_data': order_data,'monthly_order_data': monthly_order_data, 'monthly_canceled_data': monthly_canceled_data,'yearly_order_data': yearly_order_data,'yearly_canceled_data': yearly_canceled_data, 'year': year, 'month': month})
        else:
            return redirect ('r:adminlogin')
    return redirect ('r:adminlogin')


    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminuser(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            element = request.POST.get('search')
            users = Custom_User.objects.filter(name__icontains=element)
            return render(request, 'adminuser.html', {'users': users})
        else:
            users = Custom_User.objects.all()
            paginator = Paginator(users,6)
            page_number = request.GET.get('page')
            users = paginator.get_page(page_number)
            return render(request, 'adminuser.html', {'users': users})
    else:
        return redirect('r:adminlogin')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_block(request,user_id):
    user = Custom_User.objects.get(pk=user_id)
    user.user.is_active = False
    user.user.save()
    return redirect('a:adminuser')  


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def user_unblock(request,user_id):
    user = Custom_User.objects.get(pk=user_id)
    user.user.is_active = True
    user.user.save()
    return redirect('a:adminuser')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admincategory(request):
    if request.user.is_superuser:
        obj = Category.objects.all()
        return render (request,'admincategory.html',{'obj':obj})
    return redirect('u:home')




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def categorylist(request):
    if request.user.is_superuser:
        cate_id = request.GET.get('cate_id')
        obj = Category.objects.get(id=cate_id)
        if obj.listt:
            obj.listt = False
        else:
            obj.listt = True
        obj.save()
        return redirect('a:categorymanagement')
    return redirect('u:home')




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def productlist(request):
    if request.user.is_superuser:
        prod_id = request.GET.get('prod_id')
        obj = Product.objects.get(id=prod_id)
        if obj.listt:
            obj.listt = False
        else:
            obj.listt = True
        obj.save()
        return redirect('a:productmanagement')
    return redirect('u:home')




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminproduct(request):
    if request.user.is_superuser:
        products = Product.objects.all()
        paginator = Paginator(products,4)
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)
        return render(request, 'adminproduct.html', {'products': products})
    return redirect('u:home')




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def addcategory(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST.get('category_name')
            description = request.POST.get('category_description')
            obj = Category.objects.create(name=name,description = description)
            return redirect('a:categorymanagement')
        return render(request,'addcategory.html')
    return redirect('u:home')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def editcategory(request):
    if request.user.is_superuser:
        category_id = request.GET.get('cate_id')
        obj = Category.objects.get(id=category_id)
        if request.method == 'POST':
            name = request.POST.get('category_name')
            description = request.POST.get('category_description')
            obj.name = name
            obj.description = description
            obj.save()
            return redirect('a:categorymanagement')
        return render(request,'editcategory.html',{'obj':obj})
    return redirect('u:home')


@login_required
def removeimage(request,image_id):
    image = Image.objects.get(id = image_id)
    product = image.product
    image.delete()
    return redirect(reverse('a:editproduct',kwargs={'product_id':product.id}))

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def editproduct(request,product_id):
    if request.user.is_superuser:
        product = Product.objects.get(pk=product_id)
        if request.method == "POST":
            name = request.POST.get('productName')
            price = float(request.POST.get('productPrice'))
            stock = int(request.POST.get('productStock'))
            description = request.POST.get('productDescription')
            category = request.POST.get('categoryy')
            image = request.FILES.getlist('productImage[]')
            err = "Negative stock value can't be allowed"
            error = "Price should be at least 100"
            if stock < 0:
                return render(request,'productedit.html',{'product': product,'err':err})
            if price < 0:
                return render(request,'productedit.html',{'product': product,'error':error})
            obj = Category.objects.get(name=category)
            product.name = name
            product.price = price
            product.stock = stock
            product.description = description
            product.category = obj
            product.save()
            for img in image:
                Image.objects.create(product=product,image=img)
            return redirect('a:productmanagement')
        values = Category.objects.all()    
        return render(request,'productedit.html',{'product': product,'values':values})
    return redirect('a:home')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def addproduct(request):
    if request.user.is_superuser:
        if request.method == 'POST':
            name = request.POST.get('productName')
            price = float(request.POST.get('productPrice'))
            stock = int(request.POST.get('productStock'))
            description = request.POST.get('productDescription')
            category = request.POST.get('productType')
            image1 = request.FILES.getlist('productImage[]')
            err = "Negative stock value can't be allowed"
            err = "Price should be at least 100"
            if stock < 0:
                return render(request,'productadd.html',{'err':err})
            if price < 0:
                return render(request,'productadd.html',{'err':err})

            obj = Category.objects.get(name=category)
            prod = Product.objects.create(
                name = name,
                price = price,
                stock=stock,
                description = description,
                discount_price = price,
                category=obj)
            for img in image1:
                Image.objects.create(image=img,product=prod)
            return redirect('a:productmanagement')
        elements = Category.objects.all()
        return render(request, 'productadd.html', {'values': elements})
    return redirect('u:home')
    


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminorder(request):
    if request.user.is_authenticated:
        orders = Order.objects.all().order_by('-time')
        paginator = Paginator(orders,6)
        page_number = request.GET.get('page')
        orders = paginator.get_page(page_number)
        return render(request,'adminorders.html',{'orders':orders})
    return redirect('r:adminlogin')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminorderdetails(request,order_id):
    if request.user.is_authenticated:
        orders = Order.objects.get(id=order_id)
        return render(request,'adminorderdetails.html',{'orders':orders})
    return redirect('r:adminlogin')




@login_required
def orderstatus(request, order_id):
    if request.method == 'POST':
        status = request.POST.get('status')
        try:
            order = Order.objects.get(pk=order_id) 
            order.status = status
            order.save()
            return redirect('a:adminorder')  
        except Order.DoesNotExist:  
            pass
    return redirect('a:adminorder')
    


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admincoupon(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            coupons = Coupons.objects.all()
            # coupons = Coupons.objects.filter(expired=False).values('code', 'description')
            return render(request, 'admincoupon.html', {'coupons': coupons})
    return redirect('r:adminlogin')



@login_required
def get_coupons(request):
    if request.user.is_superuser:
        coupons = Coupons.objects.filter(expired=False).values('code', 'description')
        return JsonResponse(list(coupons), safe=False)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=403)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def couponadd(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            count = int(request.POST.get('count'))
            code = request.POST.get('code')
            discount_price = request.POST.get('disprice')
            starting_date = datetime.now().date()
            ending_date = starting_date + timedelta(days=14)
            err = "Negative count can't be allowed"
            error = "Coupon code already exists."
            if Coupons.objects.filter(code=code).exists():
                return render(request,'couponadd.html',{'error':error})
            if count < 1:
                return render(request,'couponadd.html',{'err':err})
            obj = Coupons.objects.create(
                count=count,
                code=code,
                discount_price=discount_price,
                starting_date=starting_date,
                ending_date=ending_date
            )
            obj.save()
            return redirect('a:admincoupon')
        return render(request, 'couponadd.html')
    return redirect('r:adminlogin')


@login_required
def couponedit(request, coupon_id):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            coupon = Coupons.objects.get(id=coupon_id)  
            if request.method == 'POST':
                coupon.count = int(request.POST.get('count'))
                count = coupon.count
                coupon.code = request.POST.get('code')
                coupon.discount_price = request.POST.get('disprice')
                starting_date = request.POST.get('start')
                ending_date = request.POST.get('end')
                err = "Negative count can't be allowed"
                if count < 1:
                    return render(request,'couponedit.html',{'err':err})
                if starting_date and ending_date: 
                    starting_date = datetime.strptime(starting_date, "%Y-%m-%d").date()
                    ending_date = datetime.strptime(ending_date, "%Y-%m-%d").date()
                    coupon.starting_date = starting_date
                    coupon.ending_date = ending_date
                coupon.save()
                return redirect('a:admincoupon')
            return render(request,'couponedit.html',{'coupon':coupon})
        return redirect('r:login')
    return redirect('r:login')



@login_required
def couponremove(request,coupon_id):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            coupon = Coupons.objects.get(id=coupon_id)
            coupon.delete()
            return redirect('a:admincoupon')
        return redirect('r:adminlogin')
    return redirect('r:adminlogin')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def salesreport(request):
    if request.user.is_authenticated:
        order = Order.objects.none() 
        if request.method == 'POST':
            start = request.POST.get('start_date')
            end = request.POST.get('end_date')
            if start and end:
                start = datetime.strptime(start, '%Y-%m-%d').date()
                end = datetime.strptime(end, '%Y-%m-%d').date()
                order = Order.objects.filter(status='Delivered', date__range=(start, end))
            else:
                order = Order.objects.filter(status='Delivered')
        else:
            order = Order.objects.filter(status='Delivered')
        if 'generate_pdf' in request.POST:
            pdf_response = generate_pdf(order)
            return pdf_response

        if 'generate_excel' in request.POST: 
            excel_response = generate_excel(order)
            return excel_response
        return render(request, 'salesreport.html', {'order': order})
    return redirect('r:adminlogin')

def generate_pdf(order_queryset):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    heading_style = styles['Heading1']
    heading = "Sales Report"
    heading_paragraph = Paragraph(heading, heading_style)
    elements.append(heading_paragraph)
    elements.append(Spacer(1, 12))

    if order_queryset:
        data = [['Sl.No.', 'Name', 'Address', 'Product', 'Qty', 'Price', 'Discount', 'Total', 'Date']]
        slno = 0  # Initialize the Sl.No. counter
        for order in order_queryset:
            for product in order.product.all():
                slno += 1  # Increment Sl.No. for each product
                data.append([
                    slno,  # Use the Sl.No. counter
                    order.user.name,
                    f"{order.orderaddress.landmark} {order.orderaddress.city}",
                    product.name,
                    order.quantity,
                    product.price,
                    order.discount,
                    order.price,
                    order.date
                ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
    else:
        elements.append(Paragraph("No orders", styles['Normal']))

    doc.build(elements)
    buf.seek(0)
    return HttpResponse(buf, content_type='application/pdf')


def generate_excel(order_queryset):
    wb = openpyxl.Workbook()
    ws = wb.active

    if order_queryset:
        # Add headers
        ws.append(['Sl.No.', 'Name', 'Address', 'Product', 'Qty', 'Price', 'Discount', 'Total', 'Date'])
        
        # Add data
        sl_no = 1
        for order in order_queryset:
            for product in order.product.all():
                ws.append([
                    sl_no,
                    order.user.name,
                    f"{order.orderaddress.landmark} {order.orderaddress.city}",
                    product.name,
                    order.quantity,
                    product.price,
                    order.discount,
                    order.price,
                    order.date
                ])
                sl_no += 1
    else:
        # If no orders, add a single row indicating that
        ws.append(["No orders"])

    # Create a file-like object to save the workbook
    excel_file = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    excel_file['Content-Disposition'] = 'attachment; filename="SalesReport.xlsx"'

    # Save workbook to the file-like object
    wb.save(excel_file)

    # Return the file-like object
    return excel_file

def addoffer(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            prod = request.POST.get('selected_product')
            dis = request.POST.get('discount')
            obj = Product.objects.get(name = prod)
            obj.percentage = dis
            disc_price = obj.price - (obj.price*(int(dis)/100))
            obj.discount_price = disc_price
            obj.save()
            return redirect('a:productmanagement')
        obj = Product.objects.all()
        return render(request,'addoffer.html',{'products':obj})
    return redirect('r:adminlogin')