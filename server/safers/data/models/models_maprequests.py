import uuid

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.gis.db import models as gis_modelsq
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from rest_framework.utils.encoders import JSONEncoder

from sequences import Sequence

from safers.rmq import RMQ, RMQ_USER
from safers.rmq.exceptions import RMQException

###########
# helpers #
###########

REQUEST_ID_GENERATOR = Sequence("map_requests")

REQUEST_ID_SEPARATOR = "-"


def get_next_request_id():
    with transaction.atomic():
        next_request_id = next(REQUEST_ID_GENERATOR)
        try:
            current_site_code = get_current_site(None).profile.code
            if current_site_code:
                next_request_id = f"{current_site_code}{REQUEST_ID_SEPARATOR}{next_request_id}"
        except ObjectDoesNotExist:
            # SiteProfile _might_ not exist during tests
            pass

        return f"{next_request_id}"


class MapRequestStatus(models.TextChoices):
    PROCESSING = "PROCESSING", _("Processing")
    FAILED = "FAILED", _("Failed")
    AVAILABLE = "AVAILABLE", _("Available")


##################
# managers, etc. #
##################


class MapRequestManager(models.Manager):
    pass


class MapRequestQuerySet(models.QuerySet):
    pass


###########
# models #
##########


class MapRequest(gis_models.Model):
    class Meta:
        verbose_name = "Map Request"
        verbose_name_plural = "Map Reqeusts"

    PRECISION = 12

    objects = MapRequestManager.from_queryset(MapRequestQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    request_id = models.CharField(
        max_length=255,
        # default=get_next_request_id  (cannot use generator as default as per https://code.djangoproject.com/ticket/11390 )
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="map_requests",
        help_text=_("User that issued the MapRequest")
    )

    title = models.CharField(max_length=255)

    status = models.CharField(
        blank=False,
        null=False,
        default=MapRequestStatus.PROCESSING,
        max_length=64,
    )

    data_types = models.ManyToManyField(
        "data.DataType", related_name="map_requests"
    )

    parameters = models.JSONField(blank=True, default=dict)

    geometry = gis_models.GeometryField(
        blank=True, null=True
    )  # TODO: CAN THIS BE A GeometryCollectionField

    geometry_wkt = models.TextField(
        blank=True, null=True, help_text=_("WKT representation of geometry")
    )

    def save(self, *args, **kwargs):
        """
        automatically set the request_id & geometry_wkt when saving
        """
        if not self.request_id:
            self.request_id = get_next_request_id()

        if not self.geometry:
            self.geometry_wkt = None
        else:
            self.geometry_wkt = self.geometry.wkt

        return super().save(*args, **kwargs)

    ###################
    # RMQ interaction #
    ###################

    def invoke(self):
        """
        publish a message to RMQ in order to trigger the creation of this MapRequest's data
        (called from MapRequestViewSet.perform_create)
        """
        rmq = RMQ()

        try:
            for data_type in self.data_types.all():
                routing_key = f"request.{data_type.datatype_id}.{RMQ_USER}.{self.request_id}"

                # TODO:
                # message_body=whatever
                # rmq.publish(
                #     json.dumps(message_body, cls=JSONEncoder),
                #     routing_key,
                #     message_id,
                # )

        except Exception as e:
            msg = f"unable to publish message: {e}"
            raise RMQException(msg)

    def revoke(self):
        """
        publish a message to RMQ in order to trigger the destruction of this MapRequest's data
        (called from MapRequestViewSet.perform_destroy)
        """

        raise NotImplementedError("Unable to delete MapRequest Data")

    @classmethod
    def process_message(cls, message_body, **kwargs):

        message_properties = kwargs.get("properties", {})

        try:
            with transaction.atomic():
                pass
        except Exception as e:
            msg = f"unable to process message: {e}"
            raise RMQException(msg)
