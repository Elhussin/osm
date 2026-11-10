import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class FiscalProfileRevision(models.Model):
    """Tenant-local seller data; never a certificate or proof of compliance."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.PositiveIntegerField(unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    registration_status = models.CharField(max_length=20, choices=[("unknown", "لم يحدد"), ("registered", "مسجل في ضريبة القيمة المضافة"), ("not_registered", "غير مسجل")])
    vat_number = models.CharField(max_length=15, blank=True)
    commercial_registration = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=200, blank=True)
    building_number = models.CharField(max_length=4, blank=True)
    additional_number = models.CharField(max_length=4, blank=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=5, blank=True)
    country_code = models.CharField(max_length=2, default="SA")
    currency = models.CharField(max_length=3, default="SAR")
    reason = models.CharField(max_length=300)
    operation_key = models.UUIDField(unique=True)
    payload_digest = models.CharField(max_length=64)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gte=1, currency="SAR", country_code="SA"), name="finance_profile_scope"),
            models.CheckConstraint(condition=Q(registration_status="registered", vat_number__regex=r"^[0-9]{15}$") | Q(registration_status__in=["unknown", "not_registered"], vat_number=""), name="finance_profile_vat_shape"),
        ]
