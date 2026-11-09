from core.models import BaseModel
from django.db import models
from django.utils.text import slugify

class Attribute(BaseModel):
    """Product attributes"""
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class AttributeValue(BaseModel):
    """Product attribute values"""
    attribute = models.ForeignKey("Attribute", related_name='values', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    label = models.CharField(max_length=100, blank=True, null=True)
    unique_key = models.CharField(max_length=255, unique=True, editable=False)


    class Meta:
        unique_together = ('attribute', 'value')
        verbose_name = "Attribute Value"
        verbose_name_plural = "Attribute Values"

    def save(self, *args, **kwargs):
        # توليد label تلقائيًا لو لم يتم إدخاله
            if not self.label:
                self.label = self.value

            # المفتاح الفريد يعتمد فقط على attribute + value
            # slugify يزيل الفراغات ويحول النص لشكل ثابت وصديق لعناوين URL
            base_key = f"{self.attribute}_{self.value}"
            self.unique_key = slugify(base_key)

            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.attribute.name}: {self.label or self.value}"

