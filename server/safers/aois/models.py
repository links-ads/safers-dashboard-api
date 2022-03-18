from django.db import models
from django.contrib.gis.db import models as gis_models


class AoiManager(models.Manager):
    pass


class AoiQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class Aoi(gis_models.Model):
    class Meta:
        verbose_name = "AOI"
        verbose_name_plural = "AOIs"

    PRECISION = 12

    objects = AoiManager.from_queryset(AoiQuerySet)()

    name = models.CharField(
        max_length=128,
        blank=False,
        null=False,
        unique=True,
    )
    description = models.TextField(
        blank=True,
        null=True,
    )
    country = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )
    zoom_level = models.FloatField(
        blank=True,
        null=True,  # TODO: min/max validation
    )
    midpoint = gis_models.PointField(
        blank=True,
        null=True,
        # TODO: min/max validation (or assert geometry.contains(midpoint))
    )

    is_active = models.BooleanField(default=True)

    geometry = gis_models.GeometryField(blank=False)

    def __str__(self):
        return self.name
