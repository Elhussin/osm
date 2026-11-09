from core.utils.test_utils import BaseTenantTestCase
from .models import Customer,Interaction,Complaint,Opportunity,Task,Campaign,Document,Subscription
from django.contrib.auth import get_user_model
User = get_user_model()

class CustomerModelTest(BaseTenantTestCase):

    def test_customer_str(self):
        customer = Customer.objects.create(
            user = User.objects.create_user(username="testuser", password="testpass"),
            first_name="John",
            last_name="Doe",
            identification_number="1234567890",
            email="john.doe@example.com",
            phone="1234567890",
            date_of_birth="1990-01-01",
            customer_type="individual",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Springfield",
            postal_code="12345",
            customer_since="2020-01-01",
            is_vip=True,
            loyalty_points=100,
            accepts_marketing=True,
            registration_number="REG123456",
            tax_number="TAX123456",
            preferred_contact="email",
            website="https://example.com",
            logo="logo.png",
            description="Test customer description"
        )
        self.assertEqual(str(customer), "John Doe")

    def test_interaction_str(self):
        customer = Customer.objects.create(
            user = User.objects.create_user(username="testuser", password="testpass"),
            first_name="John",
            last_name="Doe",
            identification_number="1234567890",
            email="john.doe@example.com",
            phone="1234567890",
            date_of_birth="1990-01-01",
            customer_type="individual",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Springfield",
            postal_code="12345",
            customer_since="2020-01-01",
            is_vip=True,
            loyalty_points=100,
            accepts_marketing=True,
            registration_number="REG123456",
            tax_number="TAX123456",
            preferred_contact="email",
            website="https://example.com",
            logo="logo.png",
            description="Test customer description"
        )
        interaction = Interaction.objects.create(
            customer=customer,
            interaction_type="phone",
            notes="Test interaction notes"
        )
        def __str__(self):
            return f"{self.interaction_type.capitalize()} with {self.customer.first_name} {self.customer.last_name}"


    def test_complaint_str(self):
        customer = Customer.objects.create(
            user = User.objects.create_user(username="testuser", password="testpass"),
            first_name="John",
            last_name="Doe",
            identification_number="1234567890",
            email="john.doe@example.com",
            phone="1234567890",
            date_of_birth="1990-01-01",
            customer_type="individual",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Springfield",
            postal_code="12345",
            customer_since="2020-01-01",
            is_vip=True,
            loyalty_points=100,
            accepts_marketing=True,
            registration_number="REG123456",
            tax_number="TAX123456",
            preferred_contact="email",
            website="https://example.com",
            logo="logo.png",
            description="Test customer description"
        )
        complaint = Complaint.objects.create(
            customer=customer,
            description="Test complaint description",
            status="open"
        )
        def __str__(self):
            return f"Complaint by {self.customer.user.username}" 

        


    def test_opportunity_str(self):
        customer = Customer.objects.create(
            user = User.objects.create_user(username="testuser", password="testpass"),
            first_name="John",
            last_name="Doe",
            identification_number="1234567890",
            email="john.doe@example.com",
            phone="1234567890",
            date_of_birth="1990-01-01",
            customer_type="individual",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Springfield",
            postal_code="12345",
            customer_since="2020-01-01",
            is_vip=True,
            loyalty_points=100,
            accepts_marketing=True,
            registration_number="REG123456",
            tax_number="TAX123456",
            preferred_contact="email",
            website="https://example.com",
            logo="logo.png",
            description="Test customer description"
        )
        opportunity = Opportunity.objects.create(
            customer=customer,
            title="Test opportunity title",
            stage="lead",
            amount=1000.00
        )
        def __str__(self):
            return f"{self.title} - {self.stage}"
        
    
    def test_task_str(self):
        customer = Customer.objects.create(
            user = User.objects.create_user(username="testuser", password="testpass"),
            first_name="John",
            last_name="Doe",
            identification_number="1234567890",
            email="john.doe@example.com",
            phone="1234567890",
            date_of_birth="1990-01-01",
            customer_type="individual",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Springfield",
            postal_code="12345",
            customer_since="2020-01-01",
            is_vip=True,
            loyalty_points=100,
            accepts_marketing=True,
            registration_number="REG123456",
            tax_number="TAX123456",
            preferred_contact="email",
            website="https://example.com",
            logo="logo.png",
            description="Test customer description"
        )
        opportunity = Opportunity.objects.create(
            customer=customer,
            title="Test opportunity title",
            stage="lead",
            amount=1000.00
        )
        task = Task.objects.create(
            customer=customer,
            opportunity=opportunity,
            title="Test task title",
            description="Test task description",
            priority="medium",
            due_date="2022-01-01",
            completed=False
        )
        def __str__(self):
            return self.title

    def test_campaign_str(self):
        customer = Customer.objects.create(
            user = User.objects.create_user(username="testuser", password="testpass"),
            first_name="John",
            last_name="Doe",
            identification_number="1234567890",
            email="john.doe@example.com",
            phone="1234567890",
            date_of_birth="1990-01-01",
            customer_type="individual",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Springfield",
            postal_code="12345",
            customer_since="2020-01-01",
            is_vip=True,
            loyalty_points=100,
            accepts_marketing=True,
            registration_number="REG123456",
            tax_number="TAX123456",
            preferred_contact="email",
            website="https://example.com",
            logo="logo.png",
            description="Test customer description"
        )
        opportunity = Opportunity.objects.create(
            customer=customer,
            title="Test opportunity title",
            stage="lead",
            amount=1000.00
        )
        task = Task.objects.create(
            customer=customer,
            opportunity=opportunity,
            title="Test task title",
            description="Test task description",
            priority="medium",
            due_date="2022-01-01",
            completed=False
        )
        campaign = Campaign.objects.create(
            customer=customer,
            opportunity=opportunity,
            task=task,
            title="Test campaign title",
            description="Test campaign description",
            start_date="2022-01-01",
            end_date="2022-01-31",
            status="active"
        )
        def __str__(self):
            return self.title
        
    def test_document_str(self):
        customer = Customer.objects.create(
            user = User.objects.create_user(username="testuser", password="testpass"),
            first_name="John",
            last_name="Doe",
            identification_number="1234567890",
            email="john.doe@example.com",
            phone="1234567890",
            date_of_birth="1990-01-01",
            customer_type="individual",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Springfield",
            postal_code="12345",
            customer_since="2020-01-01",
            is_vip=True,
            loyalty_points=100,
            accepts_marketing=True,
            registration_number="REG123456",
            tax_number="TAX123456",
            preferred_contact="email",
            website="https://example.com",
            logo="logo.png",
            description="Test customer description"
        )
        opportunity = Opportunity.objects.create(
            customer=customer,
            title="Test opportunillty title",
            stage="lead",
            amount=1000.00
        )
        task = Task.objects.create(
            customer=customer,
            opportunity=opportuinity,
            title="Test task title",
            description="Test task description",
            priority="medium",
            due_date="2022-01-01",
            completed=False
        )
        document = Document.objects.create(
            customer=customer,
            opportunity=opportunity,
            task=task,
            title="Test document title",
            file="test_document.pdf"
        )
        def __str__(self):
            return self.title
