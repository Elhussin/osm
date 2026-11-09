from django.db import models

# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True)

    def hard_delete(self):
        return super().delete()

    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

class SoftDeleteMixin:
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_objects(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class SoftDeleteManager(SoftDeleteMixin, models.Manager):
    pass

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Deleted"))

    objects = SoftDeleteManager()
    
    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save()

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
