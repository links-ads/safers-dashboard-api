import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin


class EventStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    CLOSED = "CLOSED", _("Closed")


class EventManager(models.Manager):
    pass


class EventQuerySet(models.QuerySet):
    def filter_by_distance(self, target, distance=None):
        return self.filter()

    def filter_by_time(self, target, time=None):
        return self.filter()


class Event(HashableMixin, gis_models.Model):
    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"

    PRECISION = 12

    objects = EventManager.from_queryset(EventQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    people_affected = models.IntegerField(blank=True, null=True)
    causalties = models.IntegerField(blank=True, null=True)
    estimated_damage = models.FloatField(blank=True, null=True)
    geometry = gis_models.GeometryField(blank=False, null=False)
    bounding_box = gis_models.PolygonField(blank=True, null=True)
    alerts = models.ManyToManyField("alerts.Alert", related_name="events")

    @property
    def hash_source(self):
        # TODO: INCORPORATE ALERTS ID INTO HASH_SOURCE
        return self.geometry.hexewkb

    @property
    def open(self):
        return self.end_date is None

    @property
    def closed(self):
        return self.end_date is not None

    @property
    def duration(self):
        if self.closed:
            return self.end_date - self.start_date

    def save(self, *args, **kwargs):
        if self.has_hash_source_changed(self.hash_source):
            self.bounding_box = self.geometry.envelope
        return super().save(*args, **kwargs)
