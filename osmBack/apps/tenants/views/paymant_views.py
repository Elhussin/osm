from decimal import Decimal
import logging
from django.utils.translation import gettext_lazy as T
from django.db import transaction
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
import requests
from rest_framework import status
from apps.tenants.models import (
    Client,
    Payment,
    SubscriptionPlan
)
from apps.tenants.serializers import (
    CreatePaymentOrderSerializer,
)
from apps.tenants.service import (
    create_paypal_order,
    get_paypal_access_token,

)

paymant_logger = logging.getLogger('paypal')


# ==============================================================
class CreatePaymentOrderView(APIView):
    def post(self, request):
        lang=request.headers.get('accept-language')or 'en'
        serializer = CreatePaymentOrderSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.validated_data["client"]
            plan = serializer.validated_data["plan"]
            amount = serializer.validated_data["amount"]
            direction = serializer.validated_data["direction"] # string
            method = serializer.validated_data["method"]
            try:
                if method == "paypal" or method == "":
                    approval_url, order_id = create_paypal_order(
                        client, plan.id, lang,direction, amount
                    )
                    return Response({
                        "approval_url": approval_url,
                        "order_id": order_id
                    })
                else:
                    return Response(
                        {"detail": T("Payment method not supported yet.")},
                        status=400
                    )

            except Exception as e:
                paymant_logger.error(f"Error creating payment order: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==============================================================
# Complete payment after user returns from PayPal    
class PayPalExecuteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        order_id = request.data.get("order_id")  # بدلاً من payment_id
        plan_id = request.data.get("plan_id")
        client_uuid = request.data.get("client_id")
        direction = request.data.get("direction")

        # تحقق من المدخلات
        if not all([order_id, plan_id, client_uuid]):
            return Response({"error": T("Missing PayPal payment information")}, status=400)

        try:
            with transaction.atomic():
                print("statrt")
                try:
                    client = Client.objects.get(uuid=client_uuid)
                    plan = SubscriptionPlan.objects.get(id=plan_id)
                except (Client.DoesNotExist, SubscriptionPlan.DoesNotExist):
                    return Response({"error": T("Client or plan not found")}, status=400)

                # احصل على Access Token
                access_token = get_paypal_access_token()
                if not access_token:
                    paymant_logger.error("Failed to get PayPal access token")
                    return Response({"error": T("Payment verification failed")}, status=500)
                print("getToken")
                # Capture الدفع في PayPal
                capture_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
                capture_res = requests.post(capture_url, headers=headers)
                capture_data = capture_res.json()
                print("PayPal Capture Response:", capture_data)

                # تحقق من أن العملية ناجحة
                if capture_data.get("status") != "COMPLETED":
                    paymant_logger.error("Payment not completed", extra={"order_id": order_id})
                    return Response({"error": T("Payment verification failed")}, status=400)

                # إنشاء سجل الدفع في قاعدة البيانات
                payment = Payment.objects.create(
                    client=client,
                    plan=plan,
                    amount=capture_data.get("purchase_units")[0].get("payments").get("captures")[0].get("amount").get("value"),
                    currency=capture_data.get("purchase_units")[0].get("payments").get("captures")[0].get("amount").get("currency_code"),
                    method="paypal",
                    transaction_id=order_id,
                    status="success",
                    direction=direction
                )

                # تطبيق الخطة على العميل
                payment.apply_to_client()
                print("payment applied")

                paymant_logger.info(f"PayPal payment executed successfully: {order_id}")
                return Response({
                    "detail": T("Payment executed successfully"),
                    "payment_id": payment.pk
                }, status=200)

        except Exception as e:
            paymant_logger.error(f"Error executing PayPal payment: {str(e)}")
            return Response({"error": T("Payment processing failed")}, status=500)


# ==============================================================
# Official PayPal Webhook  (Not used) will use it in the future 
# ==============================================================
class PayPalWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        event = request.data
        event_type = event.get("event_type")
        paymant_logger.info(f"Received PayPal webhook: {event_type}")

        if event_type == "PAYMENT.SALE.COMPLETED":
            try:
                plan_name = event["resource"]["transactions"][0]["item_list"]["items"][0]["sku"]
                client_id = event["resource"].get("custom")
                transaction_id = event["resource"]["id"]

                client = Client.objects.get(id=client_id)
                plan = SubscriptionPlan.objects.get(name__iexact=plan_name)

                payment = Payment.objects.create(
                    client=client,
                    plan=plan,
                    amount=Decimal(plan.price),
                    currency=plan.currency,
                    method="paypal",
                    transaction_id=transaction_id,
                    status="success"
                )
                payment.apply_to_client()

                paymant_logger.info(f"Payment processed successfully for client: {client.name}")
                return Response({"status": "success"})

            except Exception as e:
                paymant_logger.error(f"Error processing PayPal webhook: {str(e)}")
                return Response({"error": str(e)}, status=400)

        return Response({"status": "ignored"})

# ==============================================================
# Cancel Payment
# ==============================================================
# from optics_tenant.config_loader import config
class PayPalCancelView(APIView):
    permission_classes = [AllowAny]
    # if config("DEBUG"):
    #     base_url = f"{config("PROTOCOL")}://{client.schema_name}.{config("FRONTEND_DOMAIN")}:{config("FRONTEND_PORT")}/{lang}"
    # else:
    #     base_url = f"{config("PROTOCOL")}://{client.schema_name}.{config("FRONTEND_DOMAIN")}/{lang}"
    def get(self, request):
        from django.shortcuts import redirect
        return redirect("base_url" + "/api/tenant/paypal/cancel")



class PaymentListView(APIView):
    def get(self, request):
        payments = Payment.objects.all()
        return Response(PaymentSerializer(payments, many=True).data)
