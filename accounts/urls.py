from django.urls import path
from .views import (
    SignUpView,
    CodeVerifyView,
    GetNewCodeView,
    UserChangeInfoView,
    UserChangePhotoView,
    LoginView,
    LogoutView,
    ForgotPasswordView,
    ResetPasswordView,
)

urlpatterns = [
    path("signup/", SignUpView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),

    path("verify/", CodeVerifyView.as_view()),
    path("new-code/", GetNewCodeView.as_view()),

    path("me/change-info/", UserChangeInfoView.as_view()),
    path("me/change-photo/", UserChangePhotoView.as_view()),

    path("password/forgot/", ForgotPasswordView.as_view()),
    path("password/reset/", ResetPasswordView.as_view()),
]
