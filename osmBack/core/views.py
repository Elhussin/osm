from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CSVImportSerializer
from django.apps import apps
from django_tenants.utils import schema_context
import csv
import io
from core.mixins.filterOptionsMixin import FilterOptionsMixin
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.fields import CharField
class CSVImportView(APIView):
    
    def post(self, request):
        serializer = CSVImportSerializer(data=request.data)
        if serializer.is_valid():
            csv_file = serializer.validated_data['csv_file']
            config = serializer.validated_data['config']

            # Security: Use schema from authenticated user's client instead of request data
            if not request.user.client:
                return Response({"error": "User is not associated with any tenant client."}, status=403)
            
            schema = request.user.client.schema_name
            app_label = config['app']
            model_name = config['model']
            foreign_keys = config.get('foreign_keys', {})

            with schema_context(schema):
                try:
                    model = apps.get_model(app_label=app_label, model_name=model_name)
                except LookupError:
                    return Response({"error": f"Model {model_name} in {app_label} not found."}, status=400)

                model_fields = {
                    f.name: f for f in model._meta.get_fields()
                    if f.concrete and not f.auto_created
                }

                reader = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
                created = 0
                failed = 0
                errors = []

                for i, row in enumerate(reader, start=2):
                    instance_data = {}

                    for field_name, field in model_fields.items():
                        if field_name not in row or not row[field_name]:
                            continue

                        if field_name in foreign_keys:
                            rel_conf = foreign_keys[field_name]
                            rel_model = apps.get_model(rel_conf['related_model'])
                            lookup_field = rel_conf['lookup_field']
                            create_if_missing = rel_conf.get("create_if_missing", False)

                            try:
                                rel_obj = rel_model.objects.get(**{lookup_field: row[field_name]})
                            except rel_model.DoesNotExist:
                                if create_if_missing:
                                    rel_obj = rel_model.objects.create(**{lookup_field: row[field_name]})
                                else:
                                    errors.append(f"⚠️ Line {i}: {field_name} '{row[field_name]}' not found.")
                                    failed += 1
                                    break
                            instance_data[field_name] = rel_obj
                        else:
                            instance_data[field_name] = row[field_name]

                    try:
                        model.objects.get_or_create(**instance_data)
                        created += 1
                    except Exception as e:
                        failed += 1
                        errors.append(f"❌ Line {i}: {str(e)}")

                return Response({
                    "created": created,
                    "failed": failed,
                    "errors": errors
                })

        return Response(serializer.errors, status=400)



from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class BaseViewSet(FilterOptionsMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    _generated_filterset_class = None  # لتجنب إعادة التوليد كل مرة

    @property
    def filterset_class(self):
        """
        يعيد الكلاس المولد مرة واحدة فقط حتى لا يتكرر إنشاؤه.
        """
        if self._generated_filterset_class is None:
            self._generated_filterset_class = super().get_filterset_class()
        return self._generated_filterset_class
    @property
    def search_fields(self):
        if getattr(self, "_search_fields", None):
            return self._search_fields
        # توليد من serializer كل الحقول النصية تلقائيًا
        return [f for f, field in self.serializer_class().fields.items() if isinstance(field, CharField)]

    @property
    def filter_fields(self):
        if getattr(self, "_filter_fields", None):
            return self._filter_fields
        # توليد كل الحقول مع lookup 'exact' تلقائيًا
        return {f: ["exact"] for f in self.serializer_class().fields.keys()}

    def get_queryset(self):
        return super().get_queryset()

