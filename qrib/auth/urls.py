from django.urls import path
from . import views

urlpatterns = [
    path('request-otp/', views.RequestOtpView.as_view(), name='request_otp'),
    path('verify-otp/', views.VerifyOtpView.as_view(), name='verify_otp'),
    path('me/', views.MeView.as_view(), name='me'),
]
