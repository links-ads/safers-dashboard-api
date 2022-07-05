import uuid

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.db import models, transaction
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.rmq.exceptions import RMQException

###########
# helpers #
###########

REQUEST_ID_SEPARATOR = "-"


def get_next_request_id():
    current_site_code = get_current_site(None).profile.code
    last_request_id = (
        MapRequest.objects.order_by("request_id").
        values_list("request_id", flat=True).last() or
        f"{REQUEST_ID_SEPARATOR}0"
    ).split(REQUEST_ID_SEPARATOR)[-1]
    next_request_id = int(last_request_id) + 1
    if current_site_code:
        return f"{current_site_code}{REQUEST_ID_SEPARATOR}{next_request_id}"
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

    request_id = models.CharField(max_length=255, default=get_next_request_id)

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
        if self.geometry is not None:
            self.geometry_wkt = self.geometry.wkt
        else:
            self.geometry_wkt = None
        return super().save(*args, **kwargs)

    ###################
    # RMQ interaction #
    ###################

    @classmethod
    def process_message(cls, message_body, **kwargs):

        message_properties = kwargs.get("properties", {})

        try:
            with transaction.atomic():
                pass
        except Exception as e:
            msg = f"unable to process_message: {e}"
            raise RMQException(msg)
