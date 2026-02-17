from django.utils import timezone,datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from baseapp.utility import check_email_or_phone
from .models import CustomUser, CodeVerify, VIA_EMAIL, VIA_PHONE, DONE,NEW,CODE_VERIFY
from .serializers import SignUpSerializer
from


class SignUpView(APIView):

    permission_classes = []

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({"success": True,"message": "Ro'yxatdan o'tildi. Tasdiqlash kodi yuborildi.","data": serializer.data,},status=status.HTTP_201_CREATED,)


class VerifyCodeView(APIView):

    permission_classes = []

    def post(self, request):
        user_input = (request.data.get("email_phone_number") or "").strip()
        code = (request.data.get("code") or "").strip()

        if not user_input:
            raise ValidationError({"email_phone_number": "Majburiy"})
        if not code:
            raise ValidationError({"code": "Majburiy"})
        if len(code) != 4 or not code.isdigit():
            raise ValidationError({"code": "Code 4 ta raqam bo'lishi kerak"})

        check_user = check_email_or_phone(user_input)

        if check_user == "email":
            auth_type = VIA_EMAIL
            user = CustomUser.objects.filter(email=user_input.lower()).first()
        elif check_user == "phone":
            auth_type = VIA_PHONE
            user = CustomUser.objects.filter(phone_number=user_input.replace(" ", "")).first()
        else:
            raise ValidationError({"email_phone_number": "Email yoki telefon kiriting"})

        if not user:
            raise ValidationError({"detail": "Foydalanuvchi topilmadi"})

        code_obj = (CodeVerify.objects.filter(user=user, verify_type=auth_type, is_active=True).order_by("-id").first())

        if not code_obj:
            raise ValidationError({"detail": "Aktiv code topilmadi. Qayta code oling."})


        if code_obj.expiration_time and timezone.now() > code_obj.expiration_time:
            code_obj.is_active = False
            code_obj.save(update_fields=["is_active"])
            raise ValidationError({"detail": "Code muddati tugagan. Qayta code oling."})


        if str(code_obj.code) != str(code):
            raise ValidationError({"detail": "Code xato"})

        code_obj.is_active = False
        code_obj.save(update_fields=["is_active"])

        user.user_status = DONE
        user.save(update_fields=["user_status"])

        refresh = RefreshToken.for_user(user)

        return Response({"success": True,"message": "Tasdiqlandi","tokens": {"refresh": str(refresh),"access": str(refresh.access_token),},},status=status.HTTP_200_OK,)


class GetNewCodeView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        user = request.user
        self.check_active_code(user)
        if user.user_status == VIA_EMAIL:
            print(f"code | {code}")

    @staticmethot
    def check_active_code(user):
        code = user.objects.filter(is_active=False,expiration_time__gte=datetime.now())
        if code.exists():
            return ValidationError({"message":"Sizda hali aktiv cod bor "})

        return True