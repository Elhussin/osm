# tenants/paypal_service.py
import paypalrestsdk
from django.conf import settings
from optics_tenant.optics_tenant.config_loader import config
import requests
from apps.tenants.models import Payment
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

paypalrestsdk.configure({
    "mode": config("PAYPAL_MODE"),
    "client_id": config("PAYPAL_CLIENT_ID"),
    "client_secret": config("PAYPAL_CLIENT_SECRET")
})

FRONTEND_URL=config("FRONTEND_URL")



def create_paypal_order(client, plan, period):
    from apps.tenants.models import PLAN_LIMITS
    from django.conf import settings
    from decouple import config

    # تحديد السعر بناءً على المدة
    price = PLAN_LIMITS[plan]['price_month'] if period == "month" else PLAN_LIMITS[plan]['price_year']

    # روابط الرجوع (مع تمرير معرف العميل لتحديده بعد الدفع)
    return_url = f"{config('FRONTEND_URL')}/paypal/processing?client_id={client.id}&plan={plan}&period={period}"
    cancel_url = f"{config('FRONTEND_URL')}/paypal/processing?client_id={client.id}&plan={plan}&period={period}"

    # إنشاء الطلب في PayPal
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": f"{plan} plan ({period})",
                    "sku": plan,
                    "price": str(price),
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": str(price),
                "currency": "USD"
            },
            "description": f"Subscription for {client.name} ({plan} - {period})",
            "custom": str(client.id)  # مهم جدًا عشان نعرف العميل
        }]
    })

    # تنفيذ الطلب
    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return str(link.href)
        raise Exception("Approval URL not found in PayPal response.")
    else:
        raise Exception(payment.error)


def calculate_duration_from_amount(payment):
    monthly_price = payment.plan.price_per_month
    months = int(payment.amount / monthly_price)
    return max(months, 1)  # على الأقل شهر واحد



def update_subscription_after_payment(client, plan,period,amount,payment_id):
    """إنشاء سجل دفع ناجح وتحديث العميل"""
    today = now().date()


    if period == "month":
        end_date = today + relativedelta(months=1)
    elif period == "year":
        end_date = today + relativedelta(years=1)
    else:
        raise ValueError("Unknown period type")

    payment = Payment.objects.create(
        client=client,
        amount=amount or 0,  
        currency="USD",
        method="paypal",
        transaction_id=payment_id,
        plan=plan,
        start_date=today,
        end_date=end_date,
        status="success"
    )

    

    payment.apply_to_client()
    return payment



def get_paypal_access_token():
    """جلب Access Token من PayPal"""
    auth = (config("PAYPAL_CLIENT_ID"), config("PAYPAL_SECRET"))
    data = {"grant_type": "client_credentials"}
    response = requests.post(
        "https://api-m.sandbox.paypal.com/v1/oauth2/token",
        auth=auth,
        data=data
    )
    return response.json().get("access_token")

def verify_paypal_transaction(transaction_id, access_token):
    """التحقق من أن العملية مكتملة"""
    url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{transaction_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    return data.get("status") == "COMPLETED"


def log_payment(client_id, plan, transaction_id, status, amount=0):
    Payment.objects.create(
        client_id=client_id,
        amount=amount,
        currency="USD",
        method="paypal",
        transaction_id=transaction_id,
        plan=plan,
        start_date=now().date(),
        end_date=now().date(),
        status=status
    )
