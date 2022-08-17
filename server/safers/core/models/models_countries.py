from django.db import models
from django.contrib.gis.db import models as gis_models


class CountryManager(models.Manager):
    pass


class Country(gis_models.Model):
    """
    boundaries of all countries; sourced from:
    https://www.naturalearthdata.com/downloads/50m-cultural-vectors/
    """
    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    objects = CountryManager()

    sovereign_name = models.CharField(max_length=128, blank=False, null=False)
    sovereign_code = models.CharField(max_length=3, blank=False, null=False)
    admin_name = models.CharField(max_length=128, blank=False, null=False)
    admin_code = models.CharField(
        max_length=3, unique=True, blank=False, null=False
    )

    geometry = gis_models.GeometryField(blank=False, null=False)

    def __str__(self):
        return self.admin_name
