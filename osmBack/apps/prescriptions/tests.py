# tests/test_prescription_viewset.py
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.prescriptions.models import PrescriptionRecord
from apps.crm.models import Customer
from django.contrib.auth import get_user_model
from apps.users.models import Role
from apps.tenants.models import Client ,SubscriptionPlan
User = get_user_model()
# class PrescriptionViewSetTests(APITestCase):

#     def setUp(self):
#         self.subscription_plan = SubscriptionPlan.objects.create(name="Test Plan")
#         self.client = Client.objects.create(name="Test_Client", plan=self.subscription_plan)
#         self.role = Role.objects.create(name="Tester")
#         # إنشاء مستخدم
#         self.user = User.objects.create_user(username="tester", password="pass", role=self.role, client=self.client)
#         # إنشاء عملاء
#         self.customer1 = Customer.objects.create(first_name="John", last_name="Doe", email="john@example.com", phone="123" ,created_by=self.user)
#         self.customer2 = Customer.objects.create(first_name="Jane", last_name="Smith", email="jane@example.com", phone="456" ,created_by=self.user)
#         # إنشاء PrescriptionRecord
#         PrescriptionRecord.objects.create(customer=self.customer1, created_by=self.user)
#         PrescriptionRecord.objects.create(customer=self.customer2, created_by=self.user)
        
#         self.url_list = reverse('prescriptionrecord-list')  # تأكد من اسم الـ router
#         self.url_filter_options = reverse('prescriptionrecord-filter-options')  # @action name

class PrescriptionViewSetTests(APITestCase):
    def setUp(self):
        # Create a subscription plan if required by Client
        self.subscription_plan = SubscriptionPlan.objects.create(name="Test Plan")

        # Create tenant with a valid schema_name and disable schema creation
        self.tenant = Client(
            name="Test Client",
            schema_name="testclient",  # must be lowercase; letters/numbers/underscores only
            plan=self.subscription_plan,  # or 'subscription_plan' if your model uses that field
        )
        self.tenant.auto_create_schema = False  # prevent creating real DB schemas in tests
        self.tenant.save()

        # Role/user
        self.role = Role.objects.create(name="Tester")
        self.user = User.objects.create_user(
            username="tester",
            password="pass",
            role=self.role,
            client=self.tenant,
        )

        # Customers tied to created_by
        self.customer1 = Customer.objects.create(
            first_name="John", last_name="Doe", email="john@example.com", phone="123",
            created_by=self.user,
            
        )
        self.customer2 = Customer.objects.create(
            first_name="Jane", last_name="Smith", email="jane@example.com", phone="456",
            created_by=self.user,
        )

        # Create prescriptions
        PrescriptionRecord.objects.create(customer=self.customer1, created_by=self.user)
        PrescriptionRecord.objects.create(customer=self.customer2, created_by=self.user)


        self.url_list = reverse('prescriptionrecord-list')  # تأكد من اسم الـ router
        self.url_filter_options = reverse('prescriptionrecord-filter-options')  # @action name

    def test_list_filter_by_customer_id(self):
        response = self.client.get(self.url_list, {"customer__id": self.customer1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['customer'], self.customer1.id)

    def test_list_filter_by_customer_email(self):
        response = self.client.get(self.url_list, {"customer__email": "jane@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['customer'], self.customer2.id)

    def test_filter_options(self):
        response = self.client.get(self.url_filter_options)
        self.assertEqual(response.status_code, 200)
        # تحقق من أن الخيارات موجودة لكل حقل
        self.assertIn("customer__id", response.data)
        self.assertIn(self.customer1.id, response.data["customer__id"])
        self.assertIn(self.customer2.id, response.data["customer__id"])
        self.assertIn("customer__email", response.data)
        self.assertIn("john@example.com", response.data["customer__email"])
        self.assertIn("jane@example.com", response.data["customer__email"])



# python manage.py test prescriptions.tests.test_prescription_viewset.PrescriptionViewSetTests


# python manage.py test prescriptions.tests.test_prescription_viewset.PrescriptionViewSetTests
# python manage.py test prescriptions.tests.PrescriptionViewSetTests
