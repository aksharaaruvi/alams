from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    listt = models.BooleanField(default = False)


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    stock = models.IntegerField()
    description = models.CharField(max_length=50)
    listt = models.BooleanField(default = False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount_price = models.IntegerField(default = 0)
    percentage = models.IntegerField(default = 0)
    

class Image(models.Model):
    image = models.ImageField(upload_to='media/',default = 0)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,related_name = 'images')



class Coupons(models.Model):
    code = models.CharField(max_length =100)
    discount_price = models.IntegerField(null=True)
    starting_date = models.DateField(null=True)
    ending_date = models.DateField(null=True)
    count = models.IntegerField(null=True)
