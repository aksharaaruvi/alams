from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Custom_User
from homebbs.models import Mywallet
from django.views.decorators.cache import cache_control
from django.contrib.auth import authenticate, login,logout
from django.shortcuts import render, redirect
import re
import secrets
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache





def send_otp(email):
    otp_code = ''.join(secrets.choice('0123456789') for i in range(6))
    print(f'Generated otp is: {otp_code}')

    send_mail(
            'Your OTP For Signup',
            f'Your OTP is:{otp_code}',
            'aksharaaruvi@gmail.com',
            [email],
            fail_silently = False
        )
    return otp_code    



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def loginpage(request):
    if request.user.is_authenticated:
        return redirect('u:home')
    if request.method == 'POST':
        email = request.POST.get('email')  
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return redirect('u:home')
            else:
                user_err = 'This user has been blocked'
                return render(request,'login.html',{'user_err':user_err})
        else:
            error = 'Invalid email or password'
            return render(request, 'login.html', {'error': error})
    return render(request, 'login.html')


def signupage(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phonenumber = request.POST.get('phone')
        password = request.POST.get('password')
        password2 = request.POST.get('confirm_password')
        code = request.POST.get('referral_code')

        if code:
            try:
                referred_user = Custom_User.objects.get(referral_code=code)
            except Custom_User.DoesNotExist:
                referred_user = None

            if referred_user:
                referred_wallet = Mywallet.objects.get_or_create(user=referred_user)[0]
                referred_wallet.amount += 500
                referred_wallet.save()



        if not name.strip():
            name_err = 'Name cannot be empty or contain only whitespace.'
            return render(request, 'signup.html', {'name_err': name_err})

        if re.search(r'\s', name):
            name_err = 'Name cannot contain spaces.'
            return render(request, 'signup.html', {'name_err': name_err})

        if Custom_User.objects.filter(email=email).exists():
            email_err = 'This email is already registered.'
            return render(request, 'signup.html', {'email_err': email_err})

        if ' ' in email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            email_err = 'please enter a valid email address .'
            return render(request,'signup.html',{'email_err':email_err})
       

        if password != password2:
            pass_err = "password does'nt match"
            return render(request,'signup.html',{'pass_err':pass_err}) 

        

        userr = {'name':name,
        'email':email,
        'phonenumber':phonenumber,
        'password':password,
        }

        # if userr:
        #     new_user_wallet = Mywallet.objects.get_or_create(user=userr)[0]
        #     new_user_wallet.amount =+ 250
        #     new_user_wallet.save()

        otp = send_otp(email)
        request.session['generated_otp'] = otp
        request.session['userr'] = userr
        return redirect ('r:otppage')       
        
        
    return render(request, 'signup.html')
    


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logoutuser(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('u:home')
    return redirect('u:home')




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signupotp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        generated_otp = request.session.get('generated_otp')
        userr = request.session.get('userr')

        name = userr['name']
        email = userr['email']
        phonenumber = userr['phonenumber']
        password = userr['password']

        if entered_otp == generated_otp:
            user = User.objects.create_user(username=email, email=email, password=password)
            custom_user = Custom_User.objects.create(
                name=name,
                email=email,
                phone_number=phonenumber,
                user=user
            )
            request.session.pop('generated_otp', None)
            return redirect('r:login')
        else:
            error = 'Entered OTP is incorrect'
            return render(request,'otppage.html',{'error':error})

    return render(request,'otppage.html')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def adminlogin(request):
    if request.user.is_superuser:
        return redirect('a:dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request,user)
            return redirect ('a:dashboard')
        else:
            return redirect('r:adminlogin')

    return render(request,'adminlogin.html')


