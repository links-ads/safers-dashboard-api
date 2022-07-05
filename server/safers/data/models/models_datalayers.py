import uuid

from django.conf import settings
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin
from safers.rmq.exceptions import RMQException


class DataLayerManager(models.Manager):
    pass


class DataLayerQuerySet(models.QuerySet):
    def filter_by_distance(self, target, distance=None):
        return self.filter()

    def filter_by_time(self, target, time=None):
        return self.filter()


class DataLayer(HashableMixin, gis_models.Model):
    class Meta:
        verbose_name = "Data Layer"
        verbose_name_plural = "Data Layers"

    PRECISION = 12

    objects = DataLayerManager.from_queryset(DataLayerQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    external_id = models.CharField(
        max_length=128,
        unique=True,
        blank=False,
        null=False,
    )

    data = models.JSONField(default=dict)

    geometry = gis_models.GeometryField(blank=False, null=False)
    bounding_box = gis_models.PolygonField(blank=True, null=True)

    def __str__(self):
        return self.external_id

    @property
    def hash_source(self):
        if self.geometry:
            return self.geometry.hexewkb

    def save(self, *args, **kwargs):
        if self.hash_source and self.has_hash_source_changed(self.hash_source):
            if self.geometry.geom_type != "Point":
                self.bounding_box = self.geometry.envelope
        return super().save(*args, **kwargs)


##########################
# sample message payload #
##########################
"""
{
    "metadata_id": "ce0be820-a562-463a-847f-d0acca3c3385",
    "id": "6fc4a154-6ff3-44f4-b4cc-8cd352f8537c",
    "datatype_id": 33001,
    "action": "create",
    "dateOfCreation": "2019-05-28T16:48:02",
    "start": "2019-05-12T00:00:00",
    "end": "2019-05-12T00:00:00",
    "geoJSON": {
        "type": "MultiPolygon",
        "coordinates": [
            [
                [
                    [
                        16.014770306646824,
                        44.366962020791476
                    ],
                    [
                        16.014770306646824,
                        45.26319189592582
                    ],
                    [
                        19.233764447271824,
                        45.26319189592582
                    ],
                    [
                        19.233764447271824,
                        44.366962020791476
                    ],
                    [
                        16.014770306646824,
                        44.366962020791476
                    ]
                ]
            ]
        ]
    },
    "request_code": "LINKS_0",
    "url": "https://datalake-test.safers-project.cloud/dataset/ce0be820-a562-463a-847f-d0acca3c3385/resource/6fc4a154-6ff3-44f4-b4cc-8cd352f8537c/download/fc202112030000_hres.nc"
}
"""