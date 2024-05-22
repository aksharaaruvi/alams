from django.db import models
from registrationebbs.models import Custom_User
from adminebbs.models import Product

class Cart(models.Model):
    quantity = models.IntegerField(default = 1)
    coupon = models.IntegerField(default=0)
    user = models.ForeignKey(Custom_User,on_delete=models.CASCADE,related_name='usercart')
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name = 'carts')

class Address(models.Model):
    houseno = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    landmark = models.CharField(max_length=100)
    pincode = models.CharField(max_length=100)
    name = models.CharField(max_length=50,null=True)
    phoneno = models.CharField(max_length=10,default='0000000000')
    user = models.ForeignKey(Custom_User, on_delete=models.CASCADE, related_name="user_address")

class Orderaddress(models.Model):
    houseno = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    landmark = models.CharField(max_length=100)
    pincode = models.CharField(max_length=100)
    name = models.CharField(max_length=50,null=True)
    phoneno = models.CharField(max_length=10,default='0000000000')
    user = models.ForeignKey(Custom_User, on_delete=models.CASCADE, related_name="user_orderadd")

class Order(models.Model):
    order_id = models.CharField(max_length=100, unique=True,default="")
    total_orderprice = models.DecimalField(max_digits = 10,decimal_places=2, default=0)
    price = models.DecimalField(max_digits = 10,decimal_places=2, default=0)
    date = models.DateField(auto_now=False, auto_now_add=False)
    time = models.TimeField(default='00:00:00')
    status = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=50)
    quantity = models.IntegerField(default= 1)
    discount = models.IntegerField(default=0)
    user = models.ForeignKey(Custom_User,on_delete=models.CASCADE,related_name='userorder')
    orderaddress = models.ForeignKey(Orderaddress,on_delete=models.SET_NULL,related_name='orderadd',null=True)
    product = models.ManyToManyField(Product,related_name='orderproduct')

class Wishlist(models.Model):
    user = models.ForeignKey(Custom_User,on_delete=models.CASCADE,related_name='userwish')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='productwish')

class Razorpayuser(models.Model):
    razorpay_orderid = models.CharField(max_length=100,null=True,blank=True)
    razorpay_paymentid = models.CharField(max_length=100,null=True,blank=True)
    order = models.OneToOneField(Order,on_delete=models.CASCADE,related_name='razorpay',null=True,blank=True)

class Mywallet(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2,default = 0)
    payment_type = models.CharField(max_length = 100,null = True)
    user = models.OneToOneField(Custom_User,on_delete=models.CASCADE,related_name='userwallet')

class Wallethistory(models.Model):
    TRANSACTION_CHOICES = (
        ('Credited','Credited'),
        ('Debited','Debited'),
    )
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=15,choices=TRANSACTION_CHOICES)
    date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=100,null=True)
    user = models.ForeignKey(Custom_User,on_delete=models.CASCADE,default=1)
