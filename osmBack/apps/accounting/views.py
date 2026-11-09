from apps.accounting.models import  (FinancialPeriod,
 Account,Transaction,JournalEntry,
Tax,AccountingCategory,RecurringTransaction)
from rest_framework import viewsets

from apps.accounting.serializers import (FinancialPeriodSerializer,
 AccountSerializer,TransactionSerializer,JournalEntrySerializer,
TaxSerializer,AccountingCategorySerializer,RecurringTransactionSerializer)
class FinancialPeriodViewSet(viewsets.ModelViewSet):
    queryset = FinancialPeriod.objects.all()
    serializer_class = FinancialPeriodSerializer
class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
class JournalEntryViewSet(viewsets.ModelViewSet):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
class TaxViewSet(viewsets.ModelViewSet):
    queryset = Tax.objects.all()
    serializer_class = TaxSerializer
class AccountingCategoryViewSet(viewsets.ModelViewSet):
    queryset = AccountingCategory.objects.all()
    serializer_class = AccountingCategorySerializer
class RecurringTransactionViewSet(viewsets.ModelViewSet):
    queryset = RecurringTransaction.objects.all()
    serializer_class = RecurringTransactionSerializer
# The viewsets above are used to handle HTTP requests for the models
# and return the appropriate responses in JSON format.
# They provide CRUD operations for each model, allowing users to create,
# read, update, and delete instances of the models through the API.
# These viewsets are typically registered in the URL configuration
# to create the API endpoints for the accounting application.
# This allows the frontend or other clients to interact with the accounting data
# through a RESTful API, making it easier to manage financial records,
# transactions, and other accounting-related information.
