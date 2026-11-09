from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
import uuid
from PIL import Image, PngImagePlugin
from psycopg import sql
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections, transaction, IntegrityError, ProgrammingError
from django.test import Client, TransactionTestCase, override_settings
from django.utils import timezone
from django_tenants.utils import tenant_context, schema_context
from directory.provisioning import provision_company
from directory.db_roles import grant_tenant_runtime
from access.models import Branch, AuditEvent
from access.services import create_branch, create_member, assign_role, revoke_role, set_branch_active
from clinical import services
from clinical.models import Customer, CustomerBranchAccess, Prescription, PrescriptionRevision, ExamImage
from clinical.images import normalize_image, MAX_BYTES

PASSWORD = "Synthetic-Clinical-2026!"


def image_upload():
    output = BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Comment", "synthetic-private-metadata")
    Image.new("RGB", (160, 100), "white").save(output, "PNG", pnginfo=metadata)
    return SimpleUploadedFile("synthetic-exam.png", output.getvalue(), content_type="image/png")


def measurements(**overrides):
    result = {"examined_on": timezone.localdate(), "source": "internal", "right_sphere": Decimal("0.00"), "right_cylinder": Decimal("-1.25"), "right_axis": 0, "left_sphere": None}
    result.update(overrides)
    return result


@override_settings(ALLOWED_HOSTS=["a.r06.test", "b.r06.test"], SECURE_SSL_REDIRECT=False,
                   PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ClinicalTests(TransactionTestCase):
    def setUp(self):
        connection.set_schema_to_public()
        self.a = provision_company(name="Synthetic Clinical A", domain="a.r06.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        self.b = provision_company(name="Synthetic Clinical B", domain="b.r06.test", username="owner", password=PASSWORD, operation_key=uuid.uuid4(), grant_runtime=False)
        with tenant_context(self.a):
            self.owner = get_user_model().objects.get(username="owner")
            self.main = Branch.objects.get(code="MAIN")
            self.other = create_branch(self.owner.pk, code="B02", name="Synthetic second branch")
            self.doctor = create_member(self.owner.pk, username="doctor", password=PASSWORD)
            self.doctor_grant = assign_role(self.owner.pk, user_id=self.doctor.pk, role_code="optometrist", branch_id=self.main.pk)
            self.cashier = create_member(self.owner.pk, username="cashier", password=PASSWORD)
            assign_role(self.owner.pk, user_id=self.cashier.pk, role_code="cashier", branch_id=self.main.pk)
            self.customer = services.create_customer(self.owner.pk, branch_id=self.main.pk, first_name="Synthetic", last_name="Customer", phone="٠٥٠ ١٢٣ ٤٥٦٧")
        self.login()

    def tearDown(self):
        connection.set_schema_to_public()
        super().tearDown()

    def login(self, username="owner"):
        self.client = Client()
        self.assertEqual(self.client.post("/auth/login/", {"username": username, "password": PASSWORD}, HTTP_HOST="a.r06.test").status_code, 302)

    def get(self, path, **kwargs):
        return self.client.get(path, HTTP_HOST="a.r06.test", **kwargs)

    def post(self, path, data):
        return self.client.post(path, data, HTTP_HOST="a.r06.test")

    def record(self, **kwargs):
        return services.record_prescription(self.doctor.pk, customer_id=self.customer.pk, branch_id=self.main.pk, **measurements(**kwargs))

    def test_zero_blank_and_optional_image_preserve_distinct_values(self):
        with tenant_context(self.a):
            revision = self.record()
            revision.refresh_from_db()
            self.assertEqual(revision.right_sphere, Decimal("0.00"))
            self.assertEqual(revision.right_axis, 0)
            self.assertIsNone(revision.left_sphere)
            self.assertFalse(ExamImage.objects.exists())
        response = self.get(f"/prescriptions/{revision.prescription_id}/v/1/")
        self.assertContains(response, "0.00")
        self.assertNotContains(response, ">None<")
        self.assertContains(response, "لم تُرفق صورة")

    def test_invalid_axis_quarter_steps_and_empty_record_roll_back(self):
        cases = [{"right_axis": 181}, {"right_axis": None}, {"right_sphere": Decimal("0.10")}, {"right_cylinder": None, "right_axis": 5}, {"right_sphere": None, "right_cylinder": None, "right_axis": None}, {"examined_on": timezone.localdate() + timedelta(days=1)}]
        with tenant_context(self.a):
            for values in cases:
                with self.subTest(values=values), self.assertRaises(ValidationError):
                    self.record(**values)
            self.assertEqual(Prescription.objects.count(), 0)
            self.assertEqual(PrescriptionRevision.objects.count(), 0)
            self.assertEqual(ExamImage.objects.count(), 0)

    def test_database_rejects_axis_out_of_range_and_duplicate_revision(self):
        with tenant_context(self.a):
            revision = self.record()
            for changes in ({"right_axis": 181}, {"right_cylinder": -1, "right_axis": None}):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    PrescriptionRevision.objects.filter(pk=revision.pk).update(**changes)
            duplicate = PrescriptionRevision.objects.get(pk=revision.pk)
            duplicate.pk = uuid.uuid4()
            with self.assertRaises(IntegrityError), transaction.atomic():
                duplicate.save(force_insert=True)

    def test_customer_validation_normalization_and_optimistic_edit(self):
        with tenant_context(self.a):
            self.assertEqual(self.customer.phone, "0501234567")
            updated = services.update_customer(self.owner.pk, customer_id=self.customer.pk, expected_version=1, first_name="Changed")
            self.assertEqual(updated.version, 2)
            with self.assertRaises(ValidationError):
                services.update_customer(self.owner.pk, customer_id=self.customer.pk, expected_version=1, first_name="Stale")
            for values in ({"phone": "abc"}, {"date_of_birth": timezone.localdate() + timedelta(days=1)}):
                with self.assertRaises(ValidationError):
                    services.create_customer(self.owner.pk, branch_id=self.main.pk, first_name="Invalid", **values)

    def test_identity_optional_unique_per_company_and_hidden_duplicate_not_leaked(self):
        with tenant_context(self.a):
            services.create_customer(self.owner.pk, branch_id=self.other.pk, first_name="Hidden", identifier="SYNTHETIC-ID")
        self.login("cashier")
        response = self.post("/customers/new/", {"first_name": "Duplicate", "identifier": "SYNTHETIC-ID", "branch_id": self.main.pk})
        self.assertEqual(response.status_code, 422)
        self.assertNotContains(response, "Hidden", status_code=422)
        with tenant_context(self.b):
            owner = get_user_model().objects.get(username="owner")
            main = Branch.objects.get(code="MAIN")
            self.assertIsNotNone(services.create_customer(owner.pk, branch_id=main.pk, first_name="Independent", identifier="SYNTHETIC-ID"))

    def test_branch_scope_applied_before_counts_and_sharing_does_not_expose_history(self):
        with tenant_context(self.a):
            foreign_branch_customer = services.create_customer(self.owner.pk, branch_id=self.other.pk, first_name="HiddenBranch")
            revision = services.record_prescription(self.owner.pk, customer_id=foreign_branch_customer.pk, branch_id=self.other.pk, image=image_upload(), **measurements())
        self.login("doctor")
        response = self.get("/customers/?q=HiddenBranch")
        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertEqual(self.get(f"/customers/{foreign_branch_customer.pk}/").status_code, 404)
        with tenant_context(self.a):
            services.share_customer(self.owner.pk, customer_id=foreign_branch_customer.pk, source_branch_id=self.other.pk, target_branch_id=self.main.pk)
        response = self.get(f"/customers/{foreign_branch_customer.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 0)
        self.assertEqual(self.get(f"/prescriptions/{revision.prescription_id}/v/1/").status_code, 404)
        self.assertEqual(self.get(f"/prescriptions/{revision.prescription_id}/v/1/image/").status_code, 404)

    def test_sharing_requires_owner_and_shared_master_edit_requires_all_branches(self):
        with tenant_context(self.a):
            with self.assertRaises(PermissionDenied):
                services.share_customer(self.cashier.pk, customer_id=self.customer.pk, source_branch_id=self.main.pk, target_branch_id=self.other.pk)
            services.share_customer(self.owner.pk, customer_id=self.customer.pk, source_branch_id=self.main.pk, target_branch_id=self.other.pk)
            with self.assertRaises(PermissionDenied):
                services.update_customer(self.cashier.pk, customer_id=self.customer.pk, expected_version=2, first_name="Unauthorized")

    def test_cashier_cannot_read_or_write_prescription_or_image(self):
        with tenant_context(self.a):
            revision = self.record(image=image_upload())
        self.login("cashier")
        self.assertEqual(self.get(f"/customers/{self.customer.pk}/").context["page_obj"].paginator.count, 0)
        self.assertEqual(self.post(f"/customers/{self.customer.pk}/prescriptions/new/", {"right_sphere": 0}).status_code, 403)
        for suffix in ("", "image/"):
            self.assertEqual(self.get(f"/prescriptions/{revision.prescription_id}/v/1/{suffix}").status_code, 404)

    def test_cross_company_ids_and_public_media_are_inaccessible(self):
        with schema_context("public"), connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'clinical_%%'")
            self.assertEqual(cursor.fetchall(), [])
        with tenant_context(self.a):
            revision = self.record(image=image_upload())
        foreign = Client()
        foreign.post("/auth/login/", {"username": "owner", "password": PASSWORD}, HTTP_HOST="b.r06.test")
        for path in (f"/customers/{self.customer.pk}/", f"/prescriptions/{revision.prescription_id}/v/1/", f"/prescriptions/{revision.prescription_id}/v/1/image/", "/media/eye-exam.png"):
            self.assertEqual(foreign.get(path, HTTP_HOST="b.r06.test").status_code, 404)
        self.assertEqual(Client().get(f"/prescriptions/{revision.prescription_id}/v/1/image/", HTTP_HOST="a.r06.test").status_code, 403)

    def test_valid_image_reencoded_metadata_removed_and_download_is_private(self):
        with tenant_context(self.a):
            revision = self.record(image=image_upload())
            blob = bytes(ExamImage.objects.get(revision=revision).data)
            self.assertNotIn(b"synthetic-private-metadata", blob)
            self.assertEqual(Image.open(BytesIO(blob)).format, "PNG")
            tainted = image_upload()
            tainted_data = tainted.read() + b"<script>synthetic-trailing-html</script>"
            normalized = normalize_image(SimpleUploadedFile("polyglot.png", tainted_data))
            self.assertNotIn(b"synthetic-trailing-html", normalized["data"])
            self.assertNotIn("Synthetic Customer", str(list(AuditEvent.objects.values("action", "target_id"))))
        response = self.get(f"/prescriptions/{revision.prescription_id}/v/1/image/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_corrupt_svg_oversized_and_large_dimension_images_rejected_atomically(self):
        output = BytesIO()
        Image.new("1", (6001, 10)).save(output, "PNG")
        uploads = [SimpleUploadedFile("fake.png", b"<script>bad</script>", content_type="image/png"), SimpleUploadedFile("x.svg", b"<svg></svg>"), SimpleUploadedFile("big.jpg", b"x" * (MAX_BYTES + 1)), SimpleUploadedFile("wide.png", output.getvalue())]
        with tenant_context(self.a):
            for upload in uploads:
                with self.subTest(name=upload.name), self.assertRaises(ValidationError):
                    self.record(image=upload)
            self.assertEqual(Prescription.objects.count(), 0)

    def test_photo_only_documentation_and_no_image_is_also_allowed_with_measurements(self):
        with tenant_context(self.a):
            revision = self.record(right_sphere=None, right_cylinder=None, right_axis=None, image=image_upload())
            self.assertTrue(ExamImage.objects.filter(revision=revision).exists())
            self.assertEqual(self.record().version, 1)
            self.assertTrue(services.prescription_snapshot(self.doctor.pk, prescription_id=revision.prescription_id, version=1)["documentation_only"])
        self.assertContains(self.get(f"/prescriptions/{revision.prescription_id}/v/1/"), "هذا سجل صورة توثيقية")

    def test_correction_retains_original_image_values_and_customer_snapshot(self):
        with tenant_context(self.a):
            original = self.record(image=image_upload())
            snapshot = services.prescription_snapshot(self.doctor.pk, prescription_id=original.prescription_id, version=1)
            services.update_customer(self.owner.pk, customer_id=self.customer.pk, expected_version=1, first_name="Renamed")
            corrected = services.correct_prescription(self.doctor.pk, prescription_id=original.prescription_id, expected_version=1, correction_reason="Synthetic correction", **measurements(right_sphere=Decimal("1.00")))
            self.assertEqual(corrected.version, 2)
            original.refresh_from_db()
            self.assertEqual(original.right_sphere, Decimal("0.00"))
            self.assertEqual(original.customer_snapshot["name"], "Synthetic Customer")
            self.assertEqual(corrected.customer_snapshot["name"], "Renamed")
            self.assertEqual(snapshot["right_sphere"], "0.00")
            self.assertIsNone(snapshot["left_sphere"])
            self.assertEqual(bytes(ExamImage.objects.get(revision=original).data), bytes(ExamImage.objects.get(revision=corrected).data))
            with self.assertRaises(ValidationError):
                services.correct_prescription(self.doctor.pk, prescription_id=original.prescription_id, expected_version=1, correction_reason="Stale", **measurements())

    def test_remove_or_replace_image_keeps_previous_revision(self):
        with tenant_context(self.a):
            original = self.record(image=image_upload())
            removed = services.correct_prescription(self.doctor.pk, prescription_id=original.prescription_id, expected_version=1, correction_reason="Remove from new version", image_action="remove", **measurements())
            self.assertFalse(ExamImage.objects.filter(revision=removed).exists())
            replacement = services.correct_prescription(self.doctor.pk, prescription_id=original.prescription_id, expected_version=2, correction_reason="New image", image_action="replace", image=image_upload(), **measurements())
            self.assertTrue(ExamImage.objects.filter(revision=replacement).exists())
            self.assertTrue(ExamImage.objects.filter(revision=original).exists())

    def test_revoked_role_and_disabled_branch_remove_image_access_immediately(self):
        with tenant_context(self.a):
            revision = self.record(image=image_upload())
            revoke_role(self.owner.pk, assignment_id=self.doctor_grant.pk)
        self.login("doctor")
        self.assertEqual(self.get(f"/prescriptions/{revision.prescription_id}/v/1/image/").status_code, 404)
        self.login()
        with tenant_context(self.a):
            set_branch_active(self.owner.pk, branch_id=self.main.pk, active=False)
        self.assertEqual(self.get(f"/prescriptions/{revision.prescription_id}/v/1/image/").status_code, 404)

    def test_concurrent_corrections_accept_only_one_expected_version(self):
        with tenant_context(self.a):
            original = self.record()

        def correct(index):
            connections.close_all()
            try:
                with tenant_context(self.a):
                    try:
                        services.correct_prescription(self.doctor.pk, prescription_id=original.prescription_id, expected_version=1, correction_reason=f"Synthetic {index}", **measurements())
                        return "saved"
                    except ValidationError:
                        return "stale"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(correct, range(2))), ["saved", "stale"])
        with tenant_context(self.a):
            self.assertEqual(PrescriptionRevision.objects.count(), 2)

    def test_runtime_cannot_update_or_delete_revisions_and_images(self):
        role = "r06_probe_" + uuid.uuid4().hex
        with tenant_context(self.a):
            self.record(image=image_upload())
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(sql.Identifier(role)))
                grant_tenant_runtime(cursor, self.a.schema_name, role)
            try:
                for table in ("clinical_prescriptionrevision", "clinical_examimage"):
                    for verb in ("UPDATE", "DELETE"):
                        with self.subTest(table=table, verb=verb), self.assertRaises(ProgrammingError) as error, transaction.atomic():
                            with connection.cursor() as cursor:
                                cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                                statement = sql.SQL("DELETE FROM {} WHERE false").format(sql.Identifier(table)) if verb == "DELETE" else sql.SQL("UPDATE {} SET {} = {} WHERE false").format(sql.Identifier(table), sql.Identifier("data" if table.endswith("image") else "notes"), sql.Identifier("data" if table.endswith("image") else "notes"))
                                cursor.execute(statement)
                        self.assertEqual(getattr(error.exception.__cause__, "sqlstate", None), "42501")
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))

    def test_http_invalid_form_retains_zero_and_upload_limit_rejects_request(self):
        response = self.post(f"/customers/{self.customer.pk}/prescriptions/new/", {"examined_on": timezone.localdate(), "source": "internal", "branch_id": self.main.pk, "right_sphere": "0", "right_cylinder": "-1.25", "right_axis": 181})
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, 'value="0"', status_code=422)
        oversized = SimpleUploadedFile("oversized.png", b"x" * (MAX_BYTES + 1), content_type="image/png")
        response = self.post(f"/customers/{self.customer.pk}/prescriptions/new/", {"image": oversized})
        self.assertEqual(response.status_code, 400)
