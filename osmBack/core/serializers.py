from rest_framework import serializers

class CSVImportSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    config = serializers.JSONField()
