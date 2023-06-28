import json
import re
import uuid

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rest_framework.utils.encoders import JSONEncoder

from sequences import Sequence

from safers.data.models import DataType

from safers.rmq import RMQ, RMQ_USER
from safers.rmq.exceptions import RMQException

from safers.data.constants import KILOMETERS_TO_METERS, MAX_GEOMETRY_BUFFER_SIZE, NO_GEOMETRY_BUFFER_SIZE
from safers.data.utils import meters_to_degrees

###########
# helpers #
###########

REQUEST_ID_GENERATOR = Sequence("map_requests")

REQUEST_ID_SEPARATOR = "-"

REQUEST_ROUTING_KEY_REGEX = re.compile(
    f"status\.(\w+)\.(\d+)\.{RMQ_USER}\.(.+)"
)


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


def geometry_to_feature_collection(geometry):
    """
    returns geometry as a FeatureCollection
    """
    geojson = json.loads(geometry.geojson)
    if geojson.get("type") == "GeometryCollection":
        feature_geometries = geojson.get("geometries")
    else:
        feature_geometries = [geojson]
    return {
        "type":
            "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": feature_geometry,
            }
            for feature_geometry in feature_geometries
        ]
    }  # yapf: disable


##################
# managers, etc. #
##################


class MapRequestManager(models.Manager):
    def get_by_natural_key(self, request_id):
        return self.get(request_id=request_id)


class MapRequestQuerySet(models.QuerySet):
    def any_layers_processing(self):
        return self.filter(
            Q(map_request_data_types__status=MapRequestStatus.PROCESSING),
        ).distinct()

    def any_layers_failed(self):
        return self.filter(
            Q(map_request_data_types__status=MapRequestStatus.FAILED),
        ).distinct()

    def any_layers_available(self):
        return self.filter(
            Q(map_request_data_types__status=MapRequestStatus.AVAILABLE),
        ).distinct()

    def any_layers_none(self):
        return self.filter(Q(map_request_data_types__status__is_null=True
                            ), ).distinct()

    def none_layers_processing(self):
        return self.filter(
            ~Q(map_request_data_types__status=MapRequestStatus.PROCESSING),
        ).distinct()

    def none_layers_failed(self):
        return self.filter(
            ~Q(map_request_data_types__status=MapRequestStatus.FAILED),
        ).distinct()

    def none_layers_available(self):
        return self.filter(
            ~Q(map_request_data_types__status=MapRequestStatus.AVAILABLE),
        ).distinct()

    def none_layers_none(self):
        return self.filter(~Q(map_request_data_types__status__isnull=True
                             ), ).distinct()

    def all_layers_processing(self):
        return self.filter(
            Q(map_request_data_types__status=MapRequestStatus.PROCESSING),
            ~Q(map_request_data_types__status=MapRequestStatus.FAILED),
            ~Q(map_request_data_types__status=MapRequestStatus.AVAILABLE),
            ~Q(map_request_data_types__status__isnull=True),
        ).distinct()

    def all_layers_failed(self):
        return self.filter(
            Q(map_request_data_types__status=MapRequestStatus.FAILED),
            ~Q(map_request_data_types__status=MapRequestStatus.PROCESSING),
            ~Q(map_request_data_types__status=MapRequestStatus.AVAILABLE),
            ~Q(map_request_data_types__status__isnull=True),
        ).distinct()

    def all_layers_available(self):
        return self.filter(
            Q(map_request_data_types__status=MapRequestStatus.AVAILABLE),
            ~Q(map_request_data_types__status=MapRequestStatus.PROCESSING),
            ~Q(map_request_data_types__status=MapRequestStatus.FAILED),
            ~Q(map_request_data_types__status__isnull=True),
        ).distinct()

    def all_layers_none(self):
        return self.filter(
            Q(map_request_data_types__status__isnull=True),
            ~Q(map_request_data_types__status=MapRequestStatus.PROCESSING),
            ~Q(map_request_data_types__status=MapRequestStatus.FAILED),
            ~Q(map_request_data_types__status=MapRequestStatus.AVAILABLE),
        ).distinct()


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

    data_types = models.ManyToManyField(
        DataType,
        related_name="map_requests",
        through="MapRequestDataType",
    )

    parameters = models.JSONField(blank=True, default=dict)

    geometry = gis_models.GeometryField(
        blank=True, null=True
    )  # note: this can be a GeometryCollection

    geometry_wkt = models.TextField(
        blank=True,
        null=True,
        help_text=_("WKT representation of geometry"),
    )

    geometry_features = models.JSONField(
        blank=True,
        null=True,
        help_text=_("FeatureCollection representation of geometry"),
    )

    geometry_buffer_size = models.FloatField(
        default=0,
        validators=[
            MinValueValidator(NO_GEOMETRY_BUFFER_SIZE),
            MaxValueValidator(MAX_GEOMETRY_BUFFER_SIZE)
        ],
        help_text=_(
            "area (in kilometers) to increase the geometry by when rendering the layer."
        )
    )

    geometry_extent = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        help_text=_("extent of bbox of geometry as a list"),
    )

    geometry_extent_str = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        help_text=_("extent of bbox of geometry as a string"),
    )

    geometry_buffered_extent = ArrayField(
        models.FloatField(),
        blank=True,
        default=list,
        help_text=_("extent of bbox of geometry plus buffer as a list"),
    )

    geometry_buffered_extent_str = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        help_text=_("extent of bbox of geometry plus buffer as a string"),
    )

    @property
    def category(self) -> str:
        category = self.data_types.values_list("group", flat=True).first()
        if category:
            return category.title()

    @property
    def category_info(self) -> dict:
        category_info = self.data_types.values("group", "group_info").first()
        return category_info

    def natural_key(self):
        return (self.request_id, )

    def save(self, *args, **kwargs):
        """
        automatically set the request_id & extra geometry fields when saving, 
        rather than computing it in views b/c geometric computation is expensive
        """
        if not self.request_id:
            self.request_id = get_next_request_id()

        if not self.geometry:
            self.geometry_wkt = None
            self.geometry_extent = None
            self.geometry_extent_str = None
            self.geometry_features = None
        else:
            self.geometry_wkt = self.geometry.wkt
            self.geometry_features = geometry_to_feature_collection(
                self.geometry
            )
            self.geometry_extent = self.geometry.extent
            self.geometry_extent_str = ",".join(map(str, self.geometry_extent))
            if self.geometry_buffer_size == NO_GEOMETRY_BUFFER_SIZE:
                self.geometry_buffered_extent = self.geometry_extent
                self.geometry_buffered_extent_str = self.geometry_extent_str
            else:
                buffered_geometry = self.geometry.buffer(
                    meters_to_degrees(
                        (self.geometry_buffer_size * KILOMETERS_TO_METERS),
                        latitude=self.geometry.centroid.y
                    )
                )
                self.geometry_buffered_extent = buffered_geometry.extent
                self.geometry_buffered_extent_str = ",".join(
                    map(str, self.geometry_buffered_extent)
                )

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
        message_body = {
            **self.parameters,
            "title":
                self.title,
            "geometry":
                json.loads(self.geometry.geojson) if self.geometry else None,
        }
        try:

            for data_type in self.data_types.all():

                routing_key = f"request.{data_type.datatype_id}.{RMQ_USER}.{self.request_id}"
                message_body["datatype_id"] = data_type.datatype_id

                rmq.publish(
                    json.dumps(message_body, cls=JSONEncoder),
                    routing_key,
                    self.request_id,
                )

        except Exception as e:
            msg = f"unable to publish message: {e}"
            raise RMQException(msg)

    def revoke(self):
        """
        publish a message to RMQ in order to trigger the destruction of this MapRequest's data
        (called from MapRequestViewSet.perform_destroy)
        """

        rmq = RMQ()

        # TODO: UPDATE MESSAGE ONCE DELETING A THE DATA ASSOCIATED W/ A REQUEST IS SUPPORTED
        message_body = {"description": "Deleting a MapRequest"}

        try:

            for data_type in self.data_types.all():
                routing_key = f"delete.{data_type.datatype_id}.{RMQ_USER}.{self.request_id}"

                message_body["datatype_id"] = data_type.datatype_id

                rmq.publish(
                    json.dumps(message_body, cls=JSONEncoder),
                    routing_key,
                    self.request_id,
                )

        except Exception as e:
            msg = f"unable to publish message: {e}"
            raise RMQException(msg)

    @classmethod
    def process_message(cls, message_body, **kwargs):

        method = kwargs.get("method", None)
        properties = kwargs.get("properties", {})

        try:
            routing_key = method.routing_key
            (
                app_id,
                datatype_id,
                request_id,
            ) = re.match(REQUEST_ROUTING_KEY_REGEX, routing_key).groups()

            with transaction.atomic():
                data_type = DataType.objects.get(datatype_id=datatype_id)
                map_request = MapRequest.objects.get(request_id=request_id)
                map_request_data_type = MapRequestDataType.objects.get(
                    data_type=data_type, map_request=map_request
                )

                message_type = message_body.get("type")
                if message_type == "start":
                    map_request_data_type.status = MapRequestStatus.PROCESSING
                elif message_type == "end":
                    map_request_data_type.status = MapRequestStatus.AVAILABLE

                if message_body.get("status_code") not in [200, 201, 202]:
                    map_request_data_type.status = MapRequestStatus.FAILED

                map_request_data_type.message = message_body.get("message")

                map_request_data_type.save()

        except Exception as e:
            msg = f"unable to process message: {e}"
            raise RMQException(msg)


class MapRequestDataType(models.Model):
    """
    a "through" model to add some extra fields to the relationship betweeen a DataType and a MapRequest
    """

    map_request = models.ForeignKey(
        MapRequest,
        on_delete=models.CASCADE,
        related_name="map_request_data_types"
    )
    data_type = models.ForeignKey(
        DataType,
        on_delete=models.CASCADE,
        related_name="map_request_data_types"
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    url = models.CharField(max_length=512, blank=True, null=True)
    status = models.CharField(
        max_length=64,
        choices=MapRequestStatus.choices,
        blank=True,
        null=True,
    )
    message = models.CharField(max_length=128, blank=True, null=True)


#########################
# sample status message #
#########################
{
    'datatype_id': 36001,
    'status_code': 404,
    'type': 'end',
    'name': '',
    'message': 'No images found in period 2022-09-01 - 2022-09-30.',
    'urls': ["whatever", ],
    'metadata': None
}
