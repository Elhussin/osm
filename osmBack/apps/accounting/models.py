from django.db import models
from django.contrib.auth import get_user_model
from djmoney.models.fields import MoneyField
from djmoney.money import Money


User = get_user_model()

class FinancialPeriod(models.Model):
    """ Represents a financial period (e.g., fiscal year). """
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class Account(models.Model):
    """ Represents a user's financial account with a specific currency. """
    CURRENCIES = ['USD', 'EUR', 'SAR']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    currency = models.CharField(
        max_length=3,
        choices=[(c, c) for c in CURRENCIES],  # Store currency as a 3-letter code
        default='USD'
    )

    @property
    def balance(self):
        """ Calculates the account balance based on transactions. """
        income = self.transactions.filter(transaction_type='income').aggregate(
            total=models.Sum('amount')
        )['total'] or Money(0, self.currency)

        expense = self.transactions.filter(transaction_type='expense').aggregate(
            total=models.Sum('amount')
        )['total'] or Money(0, self.currency)

        # Ensure both are Money objects before subtraction
        return Money(income or 0, self.currency) - Money(expense or 0, self.currency)

    def update_balance(self):
        """ Updates and saves the account balance. """
        total = self.transactions.aggregate(total=models.Sum('amount'))['total'] or 0
        self.balance = total  # 
        self.save()  # save the account balance to the database
        return total # This does not update the database. Consider saving if needed.


    def perform_destroy(self, instance):
        account = instance.account
        instance.delete()
        account.update_balance()

    def __str__(self):
        return f"{self.name} ({self.currency})"
    

class Tax(models.Model):
    """ Represents a tax rate applicable to transactions. """
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 5.00%
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class AccountingCategory(models.Model):
    """ Represents a transaction category (income or expense). """
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category_type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """ Represents a financial transaction within an account. """

    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.PROTECT)
    date = models.DateField()
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD', currency_field_name='amount_currency')
    transaction_type = models.CharField(max_length=7, choices=[ ('income', 'Income'),('expense', 'Expense'),])
    category = models.ForeignKey("AccountingCategory", on_delete=models.SET_NULL, null=True, blank=True)
    tax_rate = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """ Ensures the transaction uses the correct currency and updates account balance. """
        if not self.amount_currency:
            self.amount_currency = self.account.currency  # Use account's currency

        super().save(*args, **kwargs)

        # Update account balance (consider saving it to avoid recalculating often)
        self.account.update_balance()

    def __str__(self):
        return f"{self.date} - {self.amount}"


class JournalEntry(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="journal_entries")
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    debit = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    credit = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')


class RecurringTransaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency='USD')
    transaction_types = models.CharField(max_length=7, choices=[ ('income', 'Income'),('expense', 'Expense'),])
    interval = models.CharField(max_length=10, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')])
    next_execution = models.DateField()

    def process(self):
        if self.next_execution <= timezone.now().date():
            Transaction.objects.create(
                account=self.account,
                amount=self.amount,
                transaction_types=self.transaction_types,
                date=timezone.now().date(),
            )
            self.next_execution = self.calculate_next_date()
            self.save()
