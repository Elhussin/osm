from django.contrib import admin
from .models import (FinancialPeriod,
 Account,Transaction,JournalEntry,
Tax,AccountingCategory,RecurringTransaction)

admin.site.register(FinancialPeriod)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(JournalEntry)
admin.site.register(Tax)
admin.site.register(AccountingCategory)
admin.site.register(RecurringTransaction)
