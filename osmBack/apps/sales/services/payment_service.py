# services/payment_service.py
def apply_payment(invoice, amount):
    invoice.paid_amount += amount
    invoice.save(update_fields=['paid_amount'])
