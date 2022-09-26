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
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"], name="unique_country_name"
            ),
        ]
        ordering = ["country", "name"]
        verbose_name = "AOI"
        verbose_name_plural = "AOIs"

    PRECISION = 12

    objects = AoiManager.from_queryset(AoiQuerySet)()

    country = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=128,
        blank=False,
        null=False,
    )
    description = models.TextField(
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

    @property
    def geometry_extent(self):
        """
        returns extent (bbox) as a comma-separated string
        suitable for request query_params
        """
        return ",".join(map(str, self.geometry.extent))

    def __str__(self):
        if self.country:
            return f"{self.country}: {self.name}"
        return self.name
