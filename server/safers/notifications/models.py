import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.db.models import Q
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GeometryCollection
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin
from safers.core.models import Country
from safers.core.utils import CaseInsensitiveTextChoices, cap_area_to_geojson
from safers.rmq.exceptions import RMQException

# NOTIFICATIONS COME FROM THE SEMANTIC-REASONING-MODULE
# THEY ARE READ FROM RMQ AND DO NOT PERSIST OUTSIDE THE DASHBOARD


class NotificationSourceChoices(CaseInsensitiveTextChoices):
    DSS = "DSS", _("Decision Support System")
    # REPORT = "REPORT", _("Report (from chatbot)")
    # EFFIS_FWI = "EFFIS_FWI", _("FWI (from netCDF)")


class NotificationTypeChoices(CaseInsensitiveTextChoices):
    RECOMENDATION = "RECOMMENDATION", _("Recommendation (from CERTH)")
    SYSTEM = "SYSTEM NOTIFICATION", _("System Update")


class NotificationScopeChoices(CaseInsensitiveTextChoices):
    PUBLIC = "Public", _("Public")
    RESTRICTED = "Restricted", _("Restricted")


class NotificationRestrictionChoices(CaseInsensitiveTextChoices):
    CITIZEN = "Citizen", _("Citizen")
    PROFESSIONAL = "Professional", _("Professional")
    ORGANIZATION = "Organization", _("Organization")


class NotificationManager(models.Manager):
    pass


class NotificationQuerySet(models.QuerySet):
    def filter_by_user(self, user):
        """
        only return notifications that this user should have access to
        """

        lookup_expr = Q()

        if user.is_professional:
            # _all_ professionals get DSS notifications...
            lookup_expr |= Q(source=NotificationSourceChoices.DSS)
        elif user.is_citizen:
            # _no_ citizen gets DSS notifications...
            lookup_expr |= ~Q(source=NotificationSourceChoices.DSS)

        return self.filter(lookup_expr)


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
        max_length=128,
        choices=NotificationTypeChoices.choices,
        blank=True,
        null=True,
    )

    timestamp = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=128, blank=True, null=True)
    source = models.CharField(
        max_length=128,
        choices=NotificationSourceChoices.choices,
        blank=True,
        null=True,
    )

    scope = models.CharField(
        max_length=128,
        choices=NotificationScopeChoices.choices,
        blank=True,
        null=True,
    )
    restriction = models.CharField(
        max_length=128,
        choices=NotificationRestrictionChoices.choices,
        blank=True,
        null=True,
    )
    target_organization_ids = ArrayField(
        models.CharField(max_length=64),
        blank=True,
        default=list,
    )

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
    def scope_restriction(self) -> str:
        """
        returns the most-specific of scope / restriction for this notification
        """
        if self.scope == NotificationScopeChoices.PUBLIC:
            return self.scope
        elif self.scope == NotificationScopeChoices.RESTRICTED:
            if self.restriction in NotificationRestrictionChoices:
                return self.restriction

    @property
    def title(self) -> str:
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
            notifications_type = NotificationTypeChoices.RECOMENDATION
        else:
            notifications_type = None

        notifications = []

        try:
            with transaction.atomic():

                message_timestamp = message_body.get("sent")
                message_status = message_body.get("status")
                message_target_organizations = message_body.get(
                    "organizationIds", []
                )
                message_source = message_body.get("source")
                if message_source:
                    message_source = NotificationSourceChoices.find_enum(
                        message_source
                    )
                message_scope = message_body.get("scope")
                if message_scope:
                    message_scope = NotificationScopeChoices.find_enum(
                        message_scope
                    )
                message_restriction = message_body.get("restriction")
                if message_restriction:
                    message_restriction = NotificationRestrictionChoices.find_enum(
                        message_restriction
                    )

                for info in message_body["info"]:
                    from safers.notifications.serializers import NotificationSerializer

                    serializer = NotificationSerializer(
                        data={
                            "type":
                                notifications_type,
                            "timestamp":
                                message_timestamp,
                            "status":
                                message_status,
                            "source":
                                message_source,
                            "scope":
                                message_scope,
                            "restriction":
                                message_restriction,
                            "target_organizations":
                                message_target_organizations,
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
  "sender": "DSS",
  "sent": "2022-09-28T13:45:58+03:00",
  "msgType": "Notification",
  "status": "Actual",
  "areaID": "211",
  "region": "Corsica",
  "source": "DSS",
  "scope": "Restricted",
  "restriction": "Professional",
  "organizationIds": [],
  "code": [],
  "info": [
    {
      "area": [
        {
          "areaDesc": "areaDesc",
          "polygon": "42.909770773, 9.339331933 42.923494631, 9.358474376 42.957357303, 9.348033236 43.000491352, 9.343082236 43.007246911, 9.372758131 43.010004167, 9.419857226 42.987529435, 9.458136133 42.965524928, 9.45104186 42.935464638, 9.467841961 42.797585819, 9.490507822 42.767852831, 9.469360897 42.732872041, 9.457241014 42.703024996, 9.454018538 42.687716432, 9.444429026 42.666910654, 9.447281641 42.624991114, 9.473240635 42.586124143, 9.39244914 42.556359212, 9.361312838 42.610289272, 9.372093069 42.899922733, 9.402125854 42.909770773, 9.339331933"
        }
      ],
      "category": "Met",
      "description": "Identify subdivision secondary emergency access.",
      "event": "Probability of fire"
    }
  ]
}  # yapf: disable
