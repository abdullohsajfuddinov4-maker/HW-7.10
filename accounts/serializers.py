from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, VIA_EMAIL, VIA_PHONE ,NEW,DONE ,PHOTO_DONE
from baseapp.utility import check_email_or_phone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate

class SignUpSerializer(serializers.ModelSerializer):
    email_phone_number = serializers.CharField(write_only=True, required=True)

    id = serializers.UUIDField(read_only=True)
    user_auth_type = serializers.CharField(read_only=True)
    user_status = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "email_phone_number", "user_auth_type", "user_status"]

    def validate(self, data):
        return self.auth_validate(data)

    @staticmethod
    def auth_validate(data):
        user_input = (data.get("email_phone_number") or "").strip()
        if not user_input:
            raise ValidationError({"success": False, "message": "email yoki tel raqami kiritish shart"})

        check_user = check_email_or_phone(user_input)

        if check_user == "email":
            if CustomUser.objects.filter(email=user_input.lower()).exists():
                raise ValidationError({"success": False, "message": "Bu email bizda mavjud"})
            return {"email": user_input.lower(), "user_auth_type": VIA_EMAIL}

        if check_user == "phone":
            phone = user_input.replace(" ", "")
            if CustomUser.objects.filter(phone_number=phone).exists():
                raise ValidationError({"success": False, "message": "Bu tel raqam bizda mavjud"})
            return {"phone_number": phone, "user_auth_type": VIA_PHONE}

        raise ValidationError({"success": False, "message": "email yoki tel raqami kiritish shart"})

    def create(self, validated_data):

        email = validated_data.get("email")
        phone_number = validated_data.get("phone_number")

        if email:
            username = email
        else:
            username = phone_number

        user = CustomUser.objects.create(
            username=username,
            email=email,
            phone_number=phone_number,
            user_auth_type=validated_data["user_auth_type"],
        )


        code = user.create_verify_code(user.user_auth_type)


        if user.user_auth_type == VIA_EMAIL:
            print(f"email:---------------- {code}")
        else:
            print(f"phone:---------------- {code}")

        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(instance.token())
        return data

class UserChangeInfoSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password or confirm_password:
            if password != confirm_password:
                raise ValidationError({"message": "parollar mos emas"})
        return data

    def validate_username(self, username):
        request = self.context.get("request")
        if request and request.user and request.user.username == username:
            return username
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Bu user allaqochon mavjud")
        return username

    def update(self, instance, validated_data):
        if instance.user_status == NEW:
            raise ValidationError({"message": "Siz tasdiqlashdan o'tmagansiz"})

        instance.username = validated_data.get("username", instance.username)
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)

        if validated_data.get("password"):
            instance.set_password(validated_data["password"])

        instance.user_status = DONE
        instance.save()
        return instance


class UserChangePhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(required=True)

    def update(self, instance, validated_data):
        instance.photo = validated_data["photo"]
        instance.user_status = PHOTO_DONE
        instance.save()
        return instance

class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise ValidationError({"message": "Login yoki parol noto'g'ri"})

        if user.user_status == NEW:
            raise ValidationError({"message": "Avval akkauntni tasdiqlang"})

        data = super().validate(attrs)
        data["user_status"] = user.user_status
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email_phone_number = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    code = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()