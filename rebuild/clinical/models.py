import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    identifier = models.CharField(max_length=30, null=True, blank=True, unique=True)
    phone = models.CharField(max_length=20, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class CustomerBranchAccess(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="branch_links")
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["customer", "branch"], name="clinical_customer_branch_unique")]


class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="prescriptions")
    branch = models.ForeignKey("access.Branch", on_delete=models.PROTECT)
    latest_version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class PrescriptionRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.PROTECT, related_name="revisions")
    version = models.PositiveIntegerField()
    examined_on = models.DateField()
    source = models.CharField(max_length=20, choices=[("internal", "فحص داخل الفرع"), ("external", "وصفة خارجية")])
    examiner = models.CharField(max_length=150, blank=True)
    right_sphere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    right_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    right_axis = models.PositiveSmallIntegerField(null=True, blank=True)
    right_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    right_pd = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    left_sphere = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    left_cylinder = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    left_axis = models.PositiveSmallIntegerField(null=True, blank=True)
    left_add = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    left_pd = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, max_length=2500)
    correction_reason = models.CharField(max_length=300, blank=True)
    customer_snapshot = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["prescription", "version"], name="clinical_revision_unique"), models.CheckConstraint(condition=Q(version__gte=1), name="clinical_revision_positive")]
        for eye in ("right", "left"):
            for part, low, high in (("sphere", -40, 40), ("cylinder", -20, 20), ("axis", 0, 180), ("add", 0, 10), ("pd", 0, 100)):
                field = f"{eye}_{part}"
                constraints.append(models.CheckConstraint(condition=Q(**{field + "__isnull": True}) | (Q(**{field + "__gte": low}) & Q(**{field + "__lte": high})), name=f"clinical_{field}_range"))
            constraints.append(models.CheckConstraint(condition=Q(**{eye + "_cylinder__isnull": True}) | Q(**{eye + "_cylinder": 0}) | Q(**{eye + "_axis__isnull": False}), name=f"clinical_{eye}_axis_required"))
        del eye, part, low, high, field


class ExamImage(models.Model):
    # Bounded, normalized bytes inside the tenant DB: no public media URL or orphan file.
    revision = models.OneToOneField(PrescriptionRevision, on_delete=models.PROTECT, primary_key=True, related_name="image")
    data = models.BinaryField()
    sha256 = models.CharField(max_length=64)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
