import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin


class AlertStatus(models.TextChoices):
    UNVALIDATED = "UNVALIDATED", _("Unvalidated")
    VALIDATED = "VALIDATED", _("Validated")
    POSSIBLE_EVENT = "POSSIBLE_EVENT", _("Possible Event")


class AlertManager(models.Manager):
    pass


class AlertQuerySet(models.QuerySet):
    def filter_by_distance(self, target, distance=None):
        return self.filter()

    def filter_by_time(self, target, time=None):
        return self.filter()


class Alert(HashableMixin, gis_models.Model):
    class Meta:
        verbose_name = "Alert"
        verbose_name_plural = "Alerts"

    PRECISION = 12

    objects = AlertManager.from_queryset(AlertQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    timestamp = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=64,
        choices=AlertStatus.choices,
        default=AlertStatus.UNVALIDATED,
        blank=True,
        null=True,
    )
    geometry = gis_models.GeometryField(blank=False, null=False)
    bounding_box = gis_models.PolygonField(blank=True, null=True)
    media = ArrayField(models.URLField(), blank=True, default=list)

    @property
    def hash_source(self):
        # TODO: INCORPORATE MESSAGE ID INTO HASH_SOURCE
        return self.geometry.hexewkb

    def save(self, *args, **kwargs):
        if self.has_hash_source_changed(self.hash_source):
            self.bounding_box = self.geometry.envelope
        return super().save(*args, **kwargs)
