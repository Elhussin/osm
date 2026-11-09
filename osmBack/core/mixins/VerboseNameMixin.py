from rest_framework import serializers

class VerboseNameMixin(serializers.Serializer):
    field_labels = serializers.SerializerMethodField()

    def get_field_labels(self, obj):
        labels = {}
        # نحصل على الحقول اللي معرفها الـ Serializer
        serializer_fields = self.Meta.fields

        for field_name in serializer_fields:
            # تجاهل الحقل الخاص بالـ labels نفسه
            if field_name == "field_labels":
                continue

            try:
                field_object = obj._meta.get_field(field_name)
                labels[field_name] = str(field_object.verbose_name)
            except Exception:
                # لو الحقل مش موجود في الـ model (مثلاً method field)
                labels[field_name] = field_name.replace("_", " ").title()

        return labels
