from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from baseapp.utility import check_email_or_phone
from .models import CustomUser, CodeVerify, VIA_EMAIL, VIA_PHONE, DONE,NEW,CODE_VERIFY
from .serializers import SignUpSerializer,UserChangeInfoSerializer,UserChangePhotoSerializer
from .serializers import LoginSerializer,LogoutSerializer,ForgotPasswordSerializer,ResetPasswordSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated ,AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView



class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny]
    queryset = CustomUser.objects.all()


class CodeVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code_value = request.data.get("code")
        if not code_value:
            raise ValidationError({"message": "code yuboring"})

        user = request.user
        self.check_code(user, code_value)

        data = {
            "status": status.HTTP_200_OK,
            "user_status": user.user_status,
            "refresh": user.token()["refresh"],
            "access": user.token()["access"],
        }
        return Response(data, status=status.HTTP_200_OK)

    @staticmethod
    def check_code(user, code_value):
        qs = user.codes.filter(
            code=code_value,
            is_active=True,
            expiration_time__gte=timezone.now()
        )
        if not qs.exists():
            raise ValidationError({"success": False, "message": "code xato yoki vaqti tugagan"})


        qs.update(is_active=False)

        if user.user_status == NEW:
            user.user_status = CODE_VERIFY
            user.save(update_fields=["user_status"])

        return True



class GetNewCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_input = (request.data.get("email_phone_number") or "").strip()
        if not user_input:
            raise ValidationError({"message": "email_phone_number yuboring"})

        kind = check_email_or_phone(user_input)

        if kind == "email":
            user = CustomUser.objects.filter(email=user_input.lower()).first()
            verify_type = VIA_EMAIL
        elif kind == "phone":
            phone = user_input.replace(" ", "")
            user = CustomUser.objects.filter(phone_number=phone).first()
            verify_type = VIA_PHONE
        else:
            raise ValidationError({"message": "email yoki tel raqami kiritish shart"})

        if not user:
            raise ValidationError({"message": "Bunday foydalanuvchi topilmadi"})

        self.check_active_code(user, verify_type)


        code = user.create_verify_code(verify_type=verify_type)

        if verify_type == VIA_EMAIL:
            print(f"email new code | {code}")
        else:
            print(f"phone new code | {code}")

        return Response({"success": True, "message": "Yangi kod yuborildi"}, status=status.HTTP_200_OK)

    @staticmethod
    def check_active_code(user, verify_type):

        active = user.codes.filter(
            verify_type=verify_type,
            is_active=True,
            expiration_time__gte=timezone.now()
        ).exists()
        if active:
            raise ValidationError({"message": "Sizda hali aktiv code bor"})
        return True


class UserChangeInfoView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserChangeInfoSerializer
    queryset = CustomUser.objects.all()

    def get_object(self):
        return self.request.user


class UserChangePhotoView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserChangePhotoSerializer

    def get_object(self):
        return self.request.user


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except Exception:
            raise ValidationError({"message": "Token noto'g'ri"})

        return Response({"success": True}, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        value = serializer.validated_data["email_phone_number"]
        kind = check_email_or_phone(value)

        if kind == "email":
            user = CustomUser.objects.filter(email=value.lower()).first()
            verify_type = VIA_EMAIL
        elif kind == "phone":
            user = CustomUser.objects.filter(phone_number=value).first()
            verify_type = VIA_PHONE
        else:
            raise ValidationError({"message": "email yoki tel raqami noto'g'ri"})

        if not user:
            raise ValidationError({"message": "Foydalanuvchi topilmadi"})

        code = user.create_verify_code(verify_type)
        print("RESET CODE:", code)

        return Response({"success": True})


class ResetPasswordView(APIView):

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        password = serializer.validated_data["new_password"]
        confirm = serializer.validated_data["confirm_password"]

        if password != confirm:
            raise ValidationError({"message": "parollar mos emas"})

        code_obj = CodeVerify.objects.filter(
            code=code,
            is_active=True,
            expiration_time__gte=timezone.now()
        ).first()

        if not code_obj:
            raise ValidationError({"message": "Code noto'g'ri yoki eskirgan"})

        user = code_obj.user
        user.set_password(password)
        user.save()

        code_obj.is_active = False
        code_obj.save()

        return Response({"success": True})