from django.urls import path
from.import views
from .views import logoutuser


app_name = 'registrationebbs'
urlpatterns = [
    path('login/',views.loginpage,name='login'),
    path('signup/',views.signupage,name='signup'),
    path('logout/',views.logoutuser,name='logout'),
    path('otppage/',views.signupotp,name='otppage'),
    path('adminlogin/',views.adminlogin,name='adminlogin'),
    path('logoutuser/',views.logoutuser,name='logoutuser'),

    # path('forgetpass/',views.forpass,name='forgetpass'),

    

] 