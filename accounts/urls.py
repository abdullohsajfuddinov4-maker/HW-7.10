from django.urls import path
from .views import SignUpView, VerifyCodeView

urlpatterns = [
    path("auth/signup/", SignUpView.as_view(), name="signup"),
    path("auth/verify/", VerifyCodeView.as_view(), name="verify"),
]
