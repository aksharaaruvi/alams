from django.db import models
from django.contrib.auth.models import User
import random
import string

class Custom_User(models.Model):
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50)  
    phone_number = models.CharField(max_length=20)
    age = models.IntegerField(default = 19) 
    gender = models.CharField(max_length=50,default = "")
    address = models.CharField(max_length=100,default = "")
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    referral_code = models.CharField(max_length=20, unique=True, null=True)


    def save(self, *args, **kwargs):
        if not self.referral_code: 
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        code_length = 10
        characters = string.ascii_letters + string.digits
        code = ''.join(random.choice(characters) for _ in range(code_length))
        return code