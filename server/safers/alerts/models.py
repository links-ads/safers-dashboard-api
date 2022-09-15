import re
import uuid

from django.contrib.gis import geos
from django.db import models, transaction
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GeometryCollection
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _

from sequences import Sequence

from safers.core.mixins import HashableMixin
from safers.core.models import Country
from safers.core.utils import CaseInsensitiveTextChoices
from safers.rmq.exceptions import RMQException

ALERT_SEQUENCE_GENERATOR = Sequence("alerts")

# TODO: AlertCategory
# “Geo” - Geophysical (inc. landslide)
# “Met” - Meteorological (inc. flood)
# “Safety” - General emergency and public safety
# “Security” - Law enforcement, military, homeland and local/private security
# “Rescue” - Rescue and recovery
# “Fire” - Fire suppression and rescue
# “Health” - Medical and public health
# “Env” - Pollution and other environmental
# “Transport” - Public and private transportation
# “Infra” - Utility, telecommunication, other non-transport infrastructure
# “CBRNE” – Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack
# “Other” - Other events


class AlertType(CaseInsensitiveTextChoices):
    UNVALIDATED = "UNVALIDATED", _("Unvalidated")
    VALIDATED = "VALIDATED", _("Validated")
    POSSIBLE_EVENT = "POSSIBLE_EVENT", _("Possible Event")


class AlertSource(CaseInsensitiveTextChoices):
    DSS = "DSS", _("Decision Support System")
    IN_SITU = "IN SITU CAMERAS", _("In-Situ Cameras")


class AlertServiceCodes(models.TextChoices):
    WEATHER_FORECAST = "WHE", _("Weather Forecast"),
    RISK = "RSK", _("Risk"),
    CAMERAS = "CMR", _("Cameras"),
    CRW_SOCIAL = "SOC", _("CRW Social"),
    DSS = "DSS", _("DSS"),
    CHATBOT = "CHT", _("Chatbot"),


ALERT_SERVICE_CODES_MAP = {
    # maps AlertSources to AlertServiceCodes
    AlertSource.IN_SITU:
        AlertServiceCodes.CAMERAS,
    AlertSource.DSS:
        AlertServiceCodes.DSS,
}


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

    sequence_number = models.PositiveBigIntegerField(blank=False, null=False)

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
    source = models.CharField(
        max_length=128, choices=AlertSource.choices, blank=True, null=True
    )
    scope = models.CharField(max_length=128, blank=True, null=True)

    media = ArrayField(
        models.URLField(max_length=512), blank=True, default=list
    )

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
        title = self.name
        if self.category:
            title += f" [{self.category}]"
        return title

    @property
    def name(self):

        service_code = ALERT_SERVICE_CODES_MAP.get(self.source)

        serial_number = f"S{self.sequence_number:0>5}"

        country = Country.objects.filter(
            geometry__intersects=self.geometry_collection
        ).first()

        return "-".join(
            map(
                str,
                filter(
                    None,
                    [
                        "ALTR",
                        service_code,
                        self.timestamp.year,
                        serial_number,
                        country.admin_code if country else None,
                    ]
                )
            )
        )

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

    def save(self, *args, **kwargs):
        if not self.sequence_number:
            self.sequence_number = next(ALERT_SEQUENCE_GENERATOR)

        return super().save(*args, **kwargs)

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

    @classmethod
    def process_message(cls, message_body, **kwargs):

        message_properties = kwargs.get("properties", {})

        message_type = message_body["msgType"]
        assert message_type.lower() == "alert", f"attempting to process {message_type} as an Alert"

        alerts = []

        try:
            with transaction.atomic():
                message_timestamp = message_body.get("sent")
                message_status = message_body.get("status")
                message_source = message_body.get("source")
                if message_source:
                    message_source = AlertSource.find_enum(message_source)
                message_scope = message_body.get("scope")
                message_category = message_body.get("category")

                for info in message_body["info"]:
                    from safers.alerts.serializers import AlertSerializer
                    serializer = AlertSerializer(
                        data={
                            "timestamp":
                                message_timestamp,
                            "status":
                                message_status,
                            "source":
                                message_source,
                            "scope":
                                message_scope,
                            "category":
                                message_category,
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
    """
    Converts the area of a CAP Alert to a GEOSGeometry.
    The format of the alert area is:
        "area": [
            {
                "areaDesc": "some circle",
                "circle" : "lat, lon radius"
            },
            {
                "areaDesc": "some polygon",
                "polygon" : "lat1, lon1 lat2, lon2... latN, lonN lat1, lon1"
            },
            {
                "areaDesc": "some point",
                "point" : "lat, lon"
            },
        ]
    """

    list_of_coords_regex = re.compile(r"(?<![,\s])\s+")

    features = []
    for area in cap_area:

        feature = {
            "type": "Feature",
            "properties": {
                "description": area.get("areaDesc")
            }
        }

        if "circle" in area:
            coords, radius = list_of_coords_regex.split(area["circle"])
            lat, lon = list(map(float, coords.split(",")))
            geometry = geos.Point(lon, lat).buffer(float(radius))
            feature["geometry"] = {
                "type": "Polygon", "coordinates": geometry.coords
            }

        elif "polygon" in area:
            coords = list_of_coords_regex.split(area["polygon"])
            remapped_coords = list(
                map(lambda x: list(map(float, x.split(",")[::-1])), coords)
            )  # convert list of strings w/ commas to list of (reversed) lists
            geometry = geos.Polygon(remapped_coords)
            feature["geometry"] = {
                "type": "Polygon", "coordinates": geometry.coords
            }

        elif "point" in area:
            lat, lon = list(map(float, area["point"].split(",")))
            geometry = geos.Point(lon, lat)
            feature["geometry"] = {
                "type": "Point", "coordinates": geometry.coords
            }

        elif "geocode" in area:
            raise ValueError("SAFERS does not support alerts w/ 'geocode'.")

        else:
            raise ValueError(f"Unknown alert area type: {area}")

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


#################
# ALERT MESSAGE #
#################

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
            "description": "There's a fire in this location",
            "area": [
                {
                    "areaDesc": "areaDesc",
                    "point" : "40.648142, 22.95255"
                }
            ]
        }
    ]
}  # yapf: disable
