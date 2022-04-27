import uuid

from django.contrib.gis import geos
from django.db import models, transaction
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin
from safers.rmq.exceptions import RMQException

# NOTIFICATIONS COME FROM THE SEMANTIC-REASONING-MODULE
# THEY ARE READ FROM RMQ AND DO NOT PERSIST OUTSIDE THE DASHBOARD


class NotificationManager(models.Manager):
    pass


class NotificationQuerySet(models.QuerySet):
    pass


class NotificationGeometry(gis_models.Model):

    PRECISION = 12

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

    def save(self, *args, **kwargs):
        if self.geometry and self.geometry.geom_type != "Point":
            self.bounding_box = self.geometry.envelope
        return super().save(*args, **kwargs)


class Notification(models.Model):
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notification"

    objects = NotificationManager.from_queryset(NotificationQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    created = models.DateTimeField(auto_now_add=True)

    timestamp = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=128, blank=True, null=True)
    source = models.CharField(max_length=128, blank=True, null=True)
    scope = models.CharField(max_length=128, blank=True, null=True)

    category = models.CharField(max_length=128, blank=True, null=True)
    event = models.CharField(max_length=128, blank=True, null=True)
    urgency = models.CharField(max_length=128, blank=True, null=True)
    severity = models.CharField(max_length=128, blank=True, null=True)
    certainty = models.CharField(max_length=128, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    message = models.JSONField(
        blank=True, null=True, help_text=_("raw message content")
    )

    @classmethod
    def process_message(cls, message_body, **kwargs):

        message_properties = kwargs.get("properties", {})

        notifications = []

        try:
            with transaction.atomic():
                for info in message_body["info"]:
                    from safers.notifications.serializers import NotificationSerializer
                    serializer = NotificationSerializer(
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
            feature["geometry"] = {
                "type":
                    "Point",
                "coordinates":
                    list(map(float, area[area_keys["Point"]].split()))
            }
        elif "Circle" in area_keys:
            x, y, radius = list(map(float, area[area_keys["Circle"]].split()))
            feature["geometry"] = {
                "type": "Polygon",
                "coordinates": geos.Point(x, y).buffer(radius).coords
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