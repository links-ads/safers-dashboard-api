import uuid

from datetime import timedelta
from itertools import chain

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GeometryCollection
from django.contrib.gis.measure import Distance as D
from django.utils.translation import gettext_lazy as _

from sequences import Sequence

from safers.core.mixins import HashableMixin
from safers.core.models import Country

EVENT_SEQUENCE_GENERATOR = Sequence("events")


class EventStatusChoices(models.TextChoices):
    ONGOING = "Ongoing", _("Ongoing")
    CLOSED = "Closed", _("Closed")


class EventManager(models.Manager):
    pass


class EventQuerySet(models.QuerySet):
    """
    contains several filters to determine if possible events overlap in time & space
    """
    def filter_by_geometry(self, target_geometry):
        distance = D(km=settings.SAFERS_POSSIBLE_EVENT_DISTANCE)
        return self.filter(
            geometry_collection__distance_lte=(target_geometry, distance)
        )

    def filter_by_timestamp(self, target_timestamp):
        delta = timedelta(hours=settings.SAFERS_POSSIBLE_EVENT_TIMERANGE)
        return self.filter(
            start_date__range=(
                target_timestamp - delta,
                target_timestamp + delta,
            )
        )

    def filter_by_alert(self, target_alert):
        distance = D(km=settings.SAFERS_POSSIBLE_EVENT_DISTANCE)
        delta = timedelta(hours=settings.SAFERS_POSSIBLE_EVENT_TIMERANGE)
        return self.filter(
            Q(
                geometry_collection__distance_lte=(
                    target_alert.geometry_collection, distance
                )
            ) & Q(
                start_date__range=(
                    target_alert.timestamp - delta,
                    target_alert.timestamp + delta
                )
            )
        )


class Event(gis_models.Model):
    """
    This is the one model that is dashboard-specific
    (ie: it isn't stored anywhere else)
    """
    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"

    PRECISION = 12
    MIN_BOUNDING_BOX_SIZE = 0.00001  # TODO: NOT SURE WHAT THIS SHOULD BE

    objects = EventManager.from_queryset(EventQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    sequence_number = models.PositiveBigIntegerField(blank=False, null=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    people_affected = models.IntegerField(blank=True, null=True)
    causalties = models.IntegerField(blank=True, null=True)
    estimated_damage = models.FloatField(blank=True, null=True)

    geometry_collection = gis_models.GeometryCollectionField(
        blank=True, null=True
    )
    bounding_box = gis_models.PolygonField(blank=True, null=True)
    center = gis_models.PointField(blank=True, null=True)

    alerts = models.ManyToManyField("alerts.Alert", related_name="events")

    @property
    def name(self):

        serial_number = f"S{self.sequence_number:0>5}"

        country = Country.objects.filter(
            # geometry__intersects=self.geometry_collection  # TODO: if geometry_collection is malformed can potentially get "GEOSIntersects: TopologyException: side location conflict"
            geometry__intersects=self.center
        ).first()

        return "-".join(
            map(
                str,
                filter(
                    None,
                    [
                        "WF",
                        self.start_date.year,
                        serial_number,
                        country.admin_code if country else None,
                    ]
                )
            )
        )

    @property
    def ongoing(self):
        return self.end_date is None

    @property
    def closed(self):
        return self.end_date is not None

    @property
    def duration(self):
        if self.closed:
            return self.end_date - self.start_date

    def recalculate_geometries(self, force_save=True):
        """
        called by signal hander in response to self.alerts being modified
        """

        geometry_collection = GeometryCollection(
            *chain.from_iterable(
                self.alerts.values_list("geometry_collection", flat=True)
            )
        )
        self.geometry_collection = geometry_collection
        self.bounding_box = geometry_collection.envelope.buffer(
            self.MIN_BOUNDING_BOX_SIZE
        ).envelope if geometry_collection.envelope.geom_type == "Point" else geometry_collection.envelope
        self.center = geometry_collection.centroid
        if force_save:
            self.save()

    def recalculate_dates(self, force_save=True):
        """
        called by signal hander in response to self.alerts being modified
        """
        earliest_date = self.alerts.all().order_by("timestamp").values_list(
            "timestamp", flat=True
        ).first()
        self.start_date = earliest_date
        if force_save:
            self.save()

    def save(self, *args, **kwargs):
        if not self.sequence_number:
            self.sequence_number = next(EVENT_SEQUENCE_GENERATOR)
        return super().save(*args, **kwargs)
