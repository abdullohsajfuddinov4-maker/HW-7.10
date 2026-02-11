import re
from rest_framework.exceptions import ValidationError


email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
phone_regex = re.compile(r"^\+998[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}$")


def check_email_or_phone(user_input):
    if re.fullmatch(email_regex, user_input):
        user_aut_type = 'email'
    elif re.fullmatch(phone_regex, user_input):
        user_aut_type = 'phone'
    else:
        data= {
            'success': False,
            'message': "Email yoki telefon raqam notohri kiritilgan"
        }
        raise ValidationError(data)
    return user_aut_type