from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class DataTypeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class DataType(models.Model):
    class Meta:
        verbose_name = "DataType"
        verbose_name_plural = "DataTypes"

    objects = DataTypeQuerySet.as_manager()

    datatype_id = models.SlugField(blank=False, null=False, unique=True)
    is_active = models.BooleanField(default=True)

    description = models.TextField(blank=True, null=True)
    group = models.CharField(max_length=128, blank=True, null=True)
    subgroup = models.CharField(max_length=128, blank=True, null=True)
    format = models.CharField(max_length=128, blank=True, null=True)
    extra_info = models.JSONField(blank=True, null=True)

    def __str__(self):
        return str(self.datatype_id)
