from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from baseapp.models import BaseModel
from django.utils import timezone
from datetime import timedelta
from config.settings import EMAIL_EXPIRATION_TIME,PHONE_EXPIRATION_TIME
import random
from rest_framework_simplejwt.tokens import RefreshToken
import uuid
# Create your models here.
ORDINARY_USER, MANAGER, ADMIN = ('ORDINARY_USER', 'MANAGER', 'ADMIN')
NEW,CODE_VERIFY,DONE,PHOTO_DONE = ('NEW','CODE_VERIFY','DONE','PHOTO_DONE')
VIA_EMAIL,VIA_PHONE = ('VIA_EMAIL','VIA_PHONE')

class CustomUser(AbstractUser,BaseModel):
    USER_ROLE = [
        (ORDINARY_USER, ORDINARY_USER),
        (ADMIN, ADMIN),
        (MANAGER, MANAGER),
    ]
    USER_STATUS = [
        (NEW,NEW),
        (CODE_VERIFY,CODE_VERIFY),
        (DONE,DONE),
        (PHOTO_DONE,PHOTO_DONE),
    ]
    UER_AUTH_TYPE = [
        (VIA_EMAIL,VIA_EMAIL),
        (VIA_PHONE,VIA_PHONE),
    ]
    user_role = models.CharField(max_length=20,choices=USER_ROLE,default=ORDINARY_USER)
    user_status = models.CharField(max_length=20,choices=USER_STATUS,default=NEW)
    email = models.EmailField(unique=True,blank=True,null=True)
    phone_number = models.CharField(max_length=13,unique=True,blank=True,null=True)
    photo = models.ImageField(upload_to='users/',default='users/default.jpg',validators=[FileExtensionValidator(allowed_extensions=['jpg','png','heic'])],blank=True,null=True)

    def __str__(self):
        return self.username

    def create_code(self, verify_type=VIA_EMAIL):
        code = ''.join([str(random.randint(1000, 9999))[-1] for _ in range(4)])
        CodeVerify.objects.create(user=self, code=code, verify_type=verify_type)
        print(f'--------------------------{code}')
        return code

    def check_username(self):
        if not self.username:
            temp_username = 'username' + uuid.uuid4().__str__().split('-')[-1]
            while CustomUser.objects.filter(username=temp_username).exists():
                temp_username = 'username' + str(random.randint(0, 10))
            self.username = temp_username

    def check_email(self):
        if self.email:
            self.email = self.email.lower()

    def check_pass(self):
        # ВАЖНО: у AbstractUser.password почти всегда НЕ пустой, но оставим логику как ты хотел
        if not self.password:
            temp_password = 'password' + uuid.uuid4().__str__().split('-')[-1]
            self.password = temp_password

    def hash_pass(self):
        # чтобы не перехешировать уже захешированный пароль
        if self.password and not self.password.startswith("pbkdf2_"):
            self.set_password(self.password)

    def clean(self):
        self.check_username()
        self.check_email()
        self.check_pass()
        self.hash_pass()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)








class CodeVerify(BaseModel):
    VERIFY_TYPE = [
        (VIA_EMAIL,VIA_EMAIL),
        (VIA_PHONE,VIA_PHONE),
    ]
    verify_type = models.CharField(max_length=20,choices=VERIFY_TYPE,default=VIA_EMAIL)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='codes')
    code = models.CharField(max_length=4,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    expiration_time = models.DateTimeField()

    def __str__(self):
        return f'{self.user} - {self.code}'

    def save(self, *args, **kwargs):
        if self.verify_type == VIA_EMAIL:
            self.expiration_time = timezone.now() + timedelta(minutes=EMAIL_EXPIRATION_TIME)
        elif self.verify_type == VIA_PHONE:
            self.expiration_time = timezone.now() + timedelta(minutes=PHONE_EXPIRATION_TIME)
        super().save(*args, **kwargs)