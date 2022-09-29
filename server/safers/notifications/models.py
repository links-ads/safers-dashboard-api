import uuid

from django.contrib.gis import geos
from django.db import models, transaction
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GeometryCollection
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin
from safers.core.models import Country
from safers.core.utils import cap_area_to_geojson
from safers.rmq.exceptions import RMQException

# NOTIFICATIONS COME FROM THE SEMANTIC-REASONING-MODULE
# THEY ARE READ FROM RMQ AND DO NOT PERSIST OUTSIDE THE DASHBOARD


class NotificationSource(models.TextChoices):
    DSS = "DSS", _("Decision Support System")
    # REPORT = "REPORT", _("Report (from chatbot)")
    # EFFIS_FWI = "EFFIS_FWI", _("FWI (from netCDF)")


class NotificationType(models.TextChoices):
    RECOMENDATION = "RECOMMENDATION", _("Recommendation (from CERTH)")
    SYSTEM = "SYSTEM NOTIFICATION", _("System Update")


class NotificationManager(models.Manager):
    pass


class NotificationQuerySet(models.QuerySet):
    pass


class NotificationGeometry(HashableMixin, gis_models.Model):
    class Meta:
        verbose_name = "Notification Geometry"
        verbose_name_plural = "Notification Geometries"

    PRECISION = 12
    MIN_BOUNDING_BOX_SIZE = 0.00001  # TODO: NOT SURE WHAT THIS SHOULD BE

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    notification = models.ForeignKey(
        "notification",
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        related_name="geometries",
    )

    description = models.TextField(blank=True, null=True)
    geometry = gis_models.GeometryField(blank=False, null=False)

    bounding_box = gis_models.PolygonField(blank=True, null=True)
    center = gis_models.PointField(blank=True, null=True)

    @property
    def hash_source(self):
        if self.geometry:
            return self.geometry.hexewkb

    def save(self, *args, **kwargs):
        geometry_updated = False
        if self.hash_source and self.has_hash_source_changed(self.hash_source):
            geometry_updated = True
            self.bounding_box = self.geometry.buffer(
                self.MIN_BOUNDING_BOX_SIZE
            ).envelope if self.geometry.geom_type == "Point" else self.geometry.envelope
            self.center = self.geometry.centroid
        super().save(*args, **kwargs)
        if geometry_updated:
            from safers.core.signals import geometry_updated as geometry_updated_signal
            geometry_updated_signal.send(
                sender=NotificationGeometry,
                geometry=self,
                parent=self.notification
            )


class Notification(models.Model):
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notification"

    PRECISION = 12

    objects = NotificationManager.from_queryset(NotificationQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    type = models.CharField(
        max_length=128, choices=NotificationType.choices, blank=True, null=True
    )

    timestamp = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=128, blank=True, null=True)
    source = models.CharField(
        max_length=128,
        choices=NotificationSource.choices,
        blank=True,
        null=True
    )
    scope = models.CharField(max_length=128, blank=True, null=True)

    category = models.CharField(max_length=128, blank=True, null=True)
    event = models.CharField(max_length=128, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )  # storing this as a string rather than a FK

    message = models.JSONField(
        blank=True, null=True, help_text=_("raw message content")
    )

    geometry_collection = gis_models.GeometryCollectionField(
        blank=True, null=True
    )
    bounding_box = gis_models.PolygonField(blank=True, null=True)
    center = gis_models.PointField(blank=True, null=True)

    @property
    def title(self):
        title = f"Notification {self.id.hex[:7]}"
        if self.category:
            title += f" [{self.category}]"
        return title

    def recalculate_geometries(self, force_save=True):
        """
        called by signal hander in response to one of the NotificationGeometries having their geometry updated
        """
        geometries_geometries = self.geometries.values(
            "geometry", "bounding_box", "center"
        )

        self.geometry_collection = GeometryCollection(
            *geometries_geometries.values_list("geometry", flat=True)
        )
        self.center = GeometryCollection(
            *geometries_geometries.values_list("center", flat=True)
        ).centroid
        self.bounding_box = GeometryCollection(
            *geometries_geometries.values_list("bounding_box", flat=True)
        ).envelope

        country = Country.objects.filter(
            # geometry__intersects=self.geometry_collection  # TODO: if geometry_collection is malformed can potentially get "GEOSIntersects: TopologyException: side location conflict"
            geometry__intersects=self.center
        ).first()
        self.country = country.admin_name if country else None

        if force_save:
            self.save()

    @classmethod
    def process_message(cls, message_body, **kwargs):

        message_properties = kwargs.get("properties", {})

        message_type = message_body["msgType"]
        assert message_type.lower() == "notification", f"attempting to process {message_type} as a Notification"

        message_sender = message_body["sender"]
        if message_sender == "DSS":
            notifications_type = NotificationType.RECOMENDATION
        else:
            notifications_type = None

        notifications = []

        try:
            with transaction.atomic():
                for info in message_body["info"]:
                    from safers.notifications.serializers import NotificationSerializer
                    serializer = NotificationSerializer(
                        data={
                            "type":
                                notifications_type,
                            "timestamp":
                                message_body.get("sent"),
                            "status":
                                message_body.get("status"),
                            "source":
                                message_body.get("source"),
                            "scope":
                                message_body.get("scope"),
                            "category":
                                info.get("category"),
                            "event":
                                info.get("event"),
                            "description":
                                info.get("description"),
                            "geometry":
                                cap_area_to_geojson(info.get("area", []))
                                ["features"],
                            "message":
                                message_body,
                        }
                    )

                    if serializer.is_valid(raise_exception=True):
                        notification = serializer.save()
                        notifications.append(notification)

        except Exception as e:
            msg = f"unable to process_message: {e}"
            raise RMQException(msg)

        return {
            "detail": [
                f"created notification: {notification}"
                for notification in notifications
            ]
        }


########################
# NOTIFICATION MESSAGE #
########################

{
    "identifier": "identifier",
    "sender": "sem",
    "sent": "2022-04-13T14:28:25+03:00",
    "status": "Actual",
    "msgType": "Notification",
    "source": "DSS",
    "scope": "Public",
    "code": [],
    "info": [
        {
            "category": "Fire ",
            "event": "Fire detection in area",
            "description": "Pay attention to the wind direction. Fires spread with the wind.",
            "area": [
                {
                    "areaDesc": "areaDesc",
                    "point" : "40.648142, 22.95255"
                }
            ]
        }
    ]
}  # yapf: disable
