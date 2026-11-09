from django.urls import path
from .views import CSVImportView

urlpatterns = [
    path('import-csv/', CSVImportView.as_view(), name='import-csv'),
]
