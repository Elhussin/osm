# tenants/paypal_service.py
import paypalrestsdk
from optics_tenant.config_loader import config
import requests
from apps.tenants.models import Payment
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

paypalrestsdk.configure({
    "mode": config("PAYPAL_MODE"),
    "client_id": config("PAYPAL_CLIENT_ID"),
    "client_secret": config("PAYPAL_CLIENT_SECRET")
})





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
    """Get Access Token from PayPal v2"""
    auth = (config("PAYPAL_CLIENT_ID"), config("PAYPAL_CLIENT_SECRET"))
    data = {"grant_type": "client_credentials"}
    response = requests.post(
        "https://api-m.sandbox.paypal.com/v1/oauth2/token",
        auth=auth,
        data=data
    )
    return response.json().get("access_token")



def create_paypal_order(client, plan, lang,direction, amount=0):
    access_token = get_paypal_access_token()
    if config("DEBUG"):
        base_url = f"{config('PROTOCOL')}://{client.schema_name}.{config('FRONTEND_DOMAIN')}:{config('FRONTEND_PORT')}/{lang}"
    else:
        base_url = f"{config('PROTOCOL')}://{client.schema_name}.{config('FRONTEND_DOMAIN')}/{lang}"

    return_url = f"{base_url}/payment/processing?client_id={client.uuid}&plan={plan}&direction={direction}"
    cancel_url = (
    f"{base_url}/payment/processing?"
    f"status=cancelled&client_id={client.uuid}&plan={plan}&direction={direction}"
)


    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": str(client.id),
                "description": f"Subscription for {client.name} ({plan} - {direction})",
                "amount": {
                    "currency_code": "USD",
                    "value": str(amount)
                }
            }
        ],
        "application_context": {
            "brand_name": "Solo Vizion",
            "landing_page": "LOGIN",
            "user_action": "PAY_NOW",
            "return_url": return_url,
            "cancel_url": cancel_url
        }
    }

    response = requests.post(
        "https://api-m.sandbox.paypal.com/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json=payload
    )

    data = response.json()
    if response.status_code in (200, 201):
        approval_url = None
        for link in data.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link["href"]
                break
        if approval_url:
            return approval_url, data["id"]  # approval_url + order_id
        else:
            raise Exception("Approval URL not found in PayPal response.")
    else:
        raise Exception(data)

def verify_paypal_transaction(order_id, access_token):
    """
    Verify PayPal order status using v2 Orders API
    """
    url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    print("verify_paypal_transaction data:", data)

    # Return 
    return data.get("status") == "COMPLETED"
