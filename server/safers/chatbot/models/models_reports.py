import uuid

from django.conf import settings
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin
from safers.rmq.exceptions import RMQException


class ReportManager(models.Manager):
    pass


class ReportQuerySet(models.QuerySet):
    def filter_by_distance(self, target, distance=None):
        return self.filter()

    def filter_by_time(self, target, time=None):
        return self.filter()


class Report(HashableMixin, gis_models.Model):
    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    PRECISION = 12

    objects = ReportManager.from_queryset(ReportQuerySet)()

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

    @classmethod
    def process_message(cls, message_body, **kwargs):
        message_properties = kwargs.get("properties", {})
        try:
            print("I AM HERE", fluh=True)
        except Exception as e:
            msg = f"unable to process_message: {e}"
            raise RMQException(msg)


##########################
# sample message payload #
##########################
"""
{
    "EntityType": "report",
    "EntityWriteAction": "create",
    "Content": {
        "Id": 10,
        "Hazard": "fire",
        "Status": "notified",
        "Location": {
            "Latitude": 45.057, "Longitude": 7.583
        },
        "Timestamp": "2021-11-11T13:21:31.082Z",
        "Address": null,
        "MediaURIs": [
            "https://safersblobstoragedev.blob.core.windows.net/reports/000010/65920fa0-7014-41a9-88e8-8a160186c6b0.jpeg"
        ],
        "ExtensionData": [{
            "CategoryId": 6, "Value": "5", "Status": "unknown"
        }],
        "Description": "Fire report",
        "Notes": null,
        "Targets": null,
        "Username": "organization.manager.test.1",
        "OrganizationName": "Organization1",
        "OrganizationId": 1,
        "Source": "chatbot",
        "IsEditable": false
    }
}
"""