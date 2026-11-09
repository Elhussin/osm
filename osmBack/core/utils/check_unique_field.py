from rest_framework import serializers

def check_unique_field(model, field_name, value, instance=None):
    queryset = model.objects.all()
    if instance and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    if queryset.filter(**{field_name: value}).exists():
        raise serializers.ValidationError(
            f"A {model.__name__} with this {field_name} already exists."
        )
    return value
