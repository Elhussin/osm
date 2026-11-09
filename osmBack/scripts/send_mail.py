
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email.',
    'hasin.taha@yahoo.com',
    ['hasin.taha@yahoo.com'],
    fail_silently=False,
)

send_mail(
    subject='Test Email',
    message='Hello, this is a test email from Django.',
    from_email='hasin.taha@yahoo.com',
    recipient_list=['hasin3112@gmail.com'],
    fail_silently=False
)





# python manage.py shell
