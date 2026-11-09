# utils/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import slugify
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.translation import gettext_lazy as _ # for translation
# from optics_tenant.optics_tenant.config_loader import config
from django.utils.translation import gettext_lazy as _
from optics_tenant.config_loader import config

FRONTEND_DOMAIN =config("FRONTEND_DOMAIN")
FRONTEND_PORT =config("FRONTEND_PORT")
PROTOCOL =config("PROTOCOL")
locale =config("LOCALE")

def send_activation_email(email, token ):
    if FRONTEND_PORT:
        activation_link = f"{PROTOCOL}://{FRONTEND_DOMAIN}:{FRONTEND_PORT}/{locale}/auth/activate/?token={token}"
    else:
        activation_link = f"{PROTOCOL}://{FRONTEND_DOMAIN}/{locale}/auth/activate/?token={token}"
    message =_(f"""
        Hi 👋,
        Please activate your account by clicking the link below:
        {activation_link}

        Note: This link will expire in 24 hours.

        Thanks,
        Solo Vizion Team
        """)
    send_mail("Activate your account", message, settings.DEFAULT_FROM_EMAIL, [email])


def send_message_acount_activated(email,schema_name,name):
    if FRONTEND_PORT:
        domain = f"{slugify(schema_name)}.{FRONTEND_DOMAIN}:{FRONTEND_PORT}/{locale}"
    else:
        domain = f"{slugify(schema_name)}.{FRONTEND_DOMAIN}/{locale}"
    message = f"""
    Hi 👋,
    Your account has been activated successfully.
    
    Your store name: {schema_name}
    Your domain: {domain}
    Your login link: {PROTOCOL}://{domain}/auth/login
    Your superuser email: {email}
    Your superuser username: {name}
    Your superuser password: ***Enter at Registration
    
    Thanks,
    Solo Vizion Team
    """
    send_mail("Account Activated", message, settings.DEFAULT_FROM_EMAIL, [email])



def send_password_reset_email(email, url):
    message = f"""
    Hi 👋,

    Please reset your password by clicking the link below:

    {url}

    Note: This link will expire in 24 hours.

    Thanks,  
    Solo Vizion Team
    """
    send_mail("Reset your password", message, settings.DEFAULT_FROM_EMAIL, [email])

def send_password_change_email(email):
    message = """
    Hi 👋,
    Your password has been changed successfully.

    Thanks,
    Solo Vizion Team
    """
    send_mail("Password Changed", message, settings.DEFAULT_FROM_EMAIL, [email])


def send_failed_activation_email(email):
    message = """
    Hi 👋,
    Your account activation failed.
    please try again by clicking previous activation link 
    """
    send_mail("Account Activation Failed", message, settings.DEFAULT_FROM_EMAIL, [email])