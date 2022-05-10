import uuid

from django.contrib.gis import geos
from django.db import models, transaction
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GeometryCollection
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin
from safers.rmq.exceptions import RMQException


class AlertType(models.TextChoices):
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


# TODO: ALERTS COME FROM...
# TODO: 1. Semantic Reasoning Module (CERTH)
# TODO: 2. IN-SITU CAMERAS (WATERVIEW)
# TODO: 3. "ELIOTSHUB" (https://alert-hub.s3.amazonaws.com/cap-feeds.html)
# TODO: MORE INFO: https://astrosat.atlassian.net/browse/SA-154?atlOrigin=eyJpIjoiMDkxMDNmOTU4ZTFlNDNjMzg2Nzk3MzkzMTEyZTk0NWQiLCJwIjoiaiJ9


class AlertGeometry(HashableMixin, gis_models.Model):
    class Meta:
        verbose_name = "Alert Geometry"
        verbose_name_plural = "Alert Geometries"

    PRECISION = 12
    MIN_BOUNDING_BOX_SIZE = 0.00001  # TODO: NOT SURE WHAT THIS SHOULD BE

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    alert = models.ForeignKey(
        "alert",
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
                sender=AlertGeometry, geometry=self, parent=self.alert
            )
            # TODO: UPDATE GEOMETRIES OF ANY ASSOCIATED EVENTS ?


class Alert(models.Model):
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

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    type = models.CharField(
        max_length=128,
        choices=AlertType.choices,
        default=AlertType.UNVALIDATED,
        blank=True,
        null=True,
    )

    timestamp = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=128, blank=True, null=True)
    source = models.CharField(max_length=128, blank=True, null=True)
    scope = models.CharField(max_length=128, blank=True, null=True)

    media = ArrayField(models.URLField(), blank=True, default=list)

    category = models.CharField(max_length=128, blank=True, null=True)
    event = models.CharField(max_length=128, blank=True, null=True)
    urgency = models.CharField(max_length=128, blank=True, null=True)
    severity = models.CharField(max_length=128, blank=True, null=True)
    certainty = models.CharField(max_length=128, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    information = models.TextField(
        blank=True,
        null=True,
        help_text=_("additional information added by dashboard user"),
    )

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
        title = f"Alert {self.id.hex[:7]}"
        if self.category:
            title += f" [{self.category}]"
        return title

    def recalculate_geometries(self, force_save=True):
        """
        called by signal hander in response to one of the AlertGeometries having their geometry updated
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
        if force_save:
            self.save()

    def validate(self):
        from safers.events.models import Event

        self.type = AlertType.VALIDATED
        self.save()

        existing_events = Event.objects.filter_by_alert(self)
        if existing_events.exists():
            # TODO: CAN THERE BE MULTIPLE existing_events ?
            created = False
            event = existing_events.first()
        else:
            created = True
            event = Event()
            event.save()
        event.alerts.add(self)

        return (event, created)

    def unvalidate(self):
        raise NotImplementedError()

    @classmethod
    def process_message(cls, message_body, **kwargs):

        message_properties = kwargs.get("properties", {})

        alerts = []

        try:
            with transaction.atomic():
                for info in message_body["info"]:
                    from safers.alerts.serializers import AlertSerializer
                    serializer = AlertSerializer(
                        data={
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
                            "urgency":
                                info.get("urgency"),
                            "severity":
                                info.get("severity"),
                            "certainty":
                                info.get("certainty"),
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
                        alert = serializer.save()
                        alerts.append(alert)

        except Exception as e:
            msg = f"unable to process_message: {e}"
            raise RMQException(msg)

        return {"detail": [f"created alert: {alert}" for alert in alerts]}


def cap_area_to_geojson(cap_area):
    features = []
    for area in cap_area:

        feature = {
            "type": "Feature",
            "properties": {
                "description": area.get("areaDesc")
            }
        }

        area_keys = {key.title(): key for key in area.keys()}

        if "Polygon" in area_keys:
            feature["geometry"] = {
                "type": "Polygon", "coordinates": area[area_keys["Polygon"]]
            }
        elif "Point" in area_keys:
            lat, lon = list(map(float, area[area_keys["Point"]].split()))
            feature["geometry"] = {
                "type": "Point", "coordinates": geos.Point(lon, lat).coords
            }
        elif "Circle" in area_keys:
            lat, lon, radius = list(map(float, area[area_keys["Circle"]].split()))
            feature["geometry"] = {
                "type": "Polygon",
                "coordinates": geos.Point(lon, lat).buffer(radius).coords
            }
        elif "Geocode" in area_keys:
            raise ValueError("don't know how to cope w/ geocode yet")
        else:
            raise ValueError("unknown area type")

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


###############
# CAP MESSAGE #
###############

{
    "identifier": "identifier",
    "sender": "sem",
    "sent": "2022-04-13T14:28:25+03:00",
    "status": "Actual",
    "msgType": "Alert",
    "source": "Report",
    "scope": "Public",
    "code": [],
    "info": [
        {
            "category": "Fire ",
            "event": "Fire detection in area",
            "urgency": "Immediate",
            "severity": "Severe",
            "certainty": "Likely",
            "description": "description",
            "area": [
                {
                    "areaDesc": "areaDesc",
                    "point" : "40.648142 22.95255"
                }
            ]
        }
    ]
}  # yapf: disable