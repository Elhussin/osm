
from core.utils.expiration_date import expiration_date
from django.utils import timezone
from datetime import timedelta

def update_client_plan(payment):
    """Update client plan limits if payment is success"""
    if payment.status != "success" or not payment.plan:
        return
    duration = payment.direction
    if duration == "month":
        duration = payment.plan.duration_months
    elif duration == "year":
        duration = payment.plan.duration_years

    client = payment.client
    client.plan = payment.plan
    client.paid_until = (client.paid_until or timezone.now().date()) + timedelta(days=int(duration))
    client.on_trial = False
    client.is_active = True
    client.apply_plan_limits()
    client.save()
