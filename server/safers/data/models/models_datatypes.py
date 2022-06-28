from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class DataTypeManager(models.Manager):
    def get_by_natural_key(self, datatype_id, subgroup, group):
        return self.get(datatype_id=datatype_id, subgroup=subgroup, group=group)

    def get_empty_subgroup(self, subgroup):
        qs = self.get_queryset()
        return qs.filter(
            datatype_id__isnull=True,
            subgroup__iexact=subgroup,
            group__isnull=True
        ).first()

    def get_empty_group(self, group):
        qs = self.get_queryset()
        return qs.filter(
            datatype_id__isnull=True,
            subgroup__isnull=True,
            group__iexact=group
        ).first()


class DataTypeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class DataType(models.Model):
    """
    Information about a data layer or category of data layer that can be displayed in the dashboard
    """
    class Meta:
        verbose_name = "DataType"
        verbose_name_plural = "DataTypes"
        constraints = [
            models.UniqueConstraint(
                fields=["datatype_id", "group", "subgroup"],
                name="unique_fields",
            ),
            models.UniqueConstraint(
                fields=["subgroup"],
                condition=Q(datatype_id__isnull=True, group__isnull=True),
                name="unique_subgroup",
            ),
            models.UniqueConstraint(
                fields=["group"],
                condition=Q(datatype_id__isnull=True, subgroup__isnull=True),
                name="unique_group",
            ),
            models.CheckConstraint(
                # either all fields are provided,
                # or only subgroup is provided,
                # or only group is provided
                check=Q(
                    datatype_id__isnull=False,
                    group__isnull=False,
                    subgroup__isnull=False,
                ) | Q(
                    datatype_id__isnull=True,
                    group__isnull=False,
                    subgroup__isnull=True,
                ) | Q(
                    datatype_id__isnull=True,
                    group__isnull=True,
                    subgroup__isnull=False,
                ),
                name="non_null_fields",
            )
        ]

    objects = DataTypeManager.from_queryset(DataTypeQuerySet)()

    datatype_id = models.SlugField(blank=True, null=True, unique=True)
    is_active = models.BooleanField(default=True)

    description = models.TextField(blank=True, null=True)
    info = models.TextField(blank=True, null=True)

    group = models.CharField(max_length=128, blank=True, null=True)
    subgroup = models.CharField(max_length=128, blank=True, null=True)
    format = models.CharField(max_length=128, blank=True, null=True)
    domain = models.CharField(max_length=64, blank=True, null=True)
    source = models.CharField(max_length=64, blank=True, null=True)
    extra_info = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def name(self):
        name = ""
        if self.datatype_id:
            name = str(self.datatype_id) + " " + name
        if self.subgroup:
            name = self.subgroup + " " + name
        if self.group:
            name = self.group + " " + name
        return name

    def natural_key(self):
        return (
            self.datatype_id,
            self.subgroup,
            self.group,
        )
