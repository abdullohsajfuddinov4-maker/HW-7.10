from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, VIA_EMAIL, VIA_PHONE
from baseapp.utility import check_email_or_phone


class SignUpSerializer(serializers.ModelSerializer):
    email_phone_number = serializers.CharField(write_only=True, required=True)

    id = serializers.UUIDField(read_only=True)
    user_auth_type = serializers.CharField(read_only=True)
    user_status = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "email_phone_number", "user_auth_type", "user_status"]

    def validate(self, attrs):
        user_input = attrs["email_phone_number"].strip()
        check_user = check_email_or_phone(user_input)

        if check_user == "email":
            email = user_input.lower()
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError({"email_phone_number": "Bu email ro'yxatdan o'tilgan!"})
            attrs["email"] = email
            attrs["user_auth_type"] = VIA_EMAIL

        elif check_user == "phone":
            phone = user_input.replace(" ", "")
            if CustomUser.objects.filter(phone_number=phone).exists():
                raise ValidationError({"email_phone_number": "Bu telefon raqami ro'yxatdan o'tilgan!"})
            attrs["phone_number"] = phone
            attrs["user_auth_type"] = VIA_PHONE

        else:
            raise ValidationError({"email_phone_number": "Email yoki telefon kiritishingiz kerak"})

        return attrs

    def create(self, validated_data):

        auth_type = validated_data.pop("user_auth_type")
        validated_data.pop("email_phone_number", None)


        if validated_data.get("email"):
            validated_data["username"] = validated_data["email"]
        else:
            validated_data["username"] = validated_data["phone_number"]
            validated_data["email"] = None

        user = CustomUser.objects.create_user(**validated_data)


        if hasattr(user, "create_verify_code"):
            code = user.create_verify_code(auth_type)
        else:
            code = user.create_code()

        if auth_type == VIA_EMAIL and user.email:
            send_mail("Tasdiqlash kodi",f"Sizning kodingiz: {code}",settings.DEFAULT_FROM_EMAIL,[user.email],fail_silently=False,)
        else:
            print(f"TEL: {user.phone_number} | KOD: {code}")
        user._auth_type = auth_type
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["user_auth_type"] = getattr(instance, "_auth_type", None)
        return data
