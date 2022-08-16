import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.core.utils import validate_schema


def validate_media(value):
    """
    A simple validator that ensures report.media is a list of correctly-formatted objects
    """

    media_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "thumbnail": {"type": "string"},
                "type": {"type": "string"}
            },
            "required": ["url"],
        }
    }  # yapf: disable

    return validate_schema(value, media_schema)


def validate_reporter(value):
    """
    A simple validator that ensures report.reporter is a correctly-formatted object
    """

    reporter_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "organization": {"type": "string"}
        },
    }  # yapf: disable

    return validate_schema(value, reporter_schema)


class ReportSourceTypes(models.TextChoices):
    CHATBOT = "Chatbot", _("Chatbot"),


class ReportHazardTypes(models.TextChoices):
    AVALANCHE = "Avalanche", _("Avalanche"),
    EARTHQUAKE = "Earthquake", _("Earthquake"),
    FIRE = "Fire", _("Fire"),
    FLOOD = "Flood", _("Flood"),
    LANDSLIDE = "Landslide", _("Landslide"),
    STORM = "Storm", _("Storm"),
    WEATHER = "Weather", _("Weather"),
    SUBSIDENCE = "Subsidence", _("Subsidence"),


class ReportStatusTypes(models.TextChoices):
    UNKNOWN = "Unknown", _("Unknown"),
    NOTIFIED = "Notified", _("Notified"),
    MANAGED = "Managed", _("Managed"),
    CLOSED = "Closed", _("Closed"),


class ReportContentTypes(models.TextChoices):
    SUBMITTED = "Submitted", _("Submitted"),
    INAPPROPRIATE = "Inappropriate", _("Inappropriate"),
    INACCURRATE = "Inaccurate", _("Inaccurate"),
    VALIDATED = "Validated", _("Validated"),


class ReportVisabilityTypes(models.TextChoices):
    PRIVATE = "Private", _("Private"),
    PUBLIC = "Public", _("Pubic"),
    ALL = "All", _("All"),


class Report(gis_models.Model):
    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"

    PRECISION = 12

    report_id = models.CharField(
        max_length=128, unique=True, blank=False, null=False
    )

    mission_id = models.CharField(max_length=128, blank=True, null=True)

    timestamp = models.DateTimeField(blank=True, null=True)
    source = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        choices=ReportSourceTypes.choices,
        default=ReportSourceTypes.CHATBOT,
    )
    hazard = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        choices=ReportHazardTypes.choices,
        default=ReportHazardTypes.FIRE,
    )
    status = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        choices=ReportStatusTypes.choices
    )
    content = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        choices=ReportContentTypes.choices
    )
    is_public = models.BooleanField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    media = models.JSONField(validators=[validate_media], default=list)
    reporter = models.JSONField(validators=[validate_reporter], default=dict)
    geometry = gis_models.GeometryField(blank=False, null=False)

    def __str__(self):
        return f"{self.report_id}"

    @property
    def name(self):
        return f"Report {self.report_id}"

    @property
    def visibility(self):
        if self.is_public:
            return ReportVisabilityTypes.PUBLIC
        return ReportVisabilityTypes.PRIVATE

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "Report is not stored in the db and therefore cannot be saved."
        )


##########################
# sample message payload #
##########################
# """
# {
#     "EntityType": "report",
#     "EntityWriteAction": "create",
#     "Content": {
#         "Id": 10,
#         "Hazard": "fire",
#         "Status": "notified",
#         "Location": {
#             "Latitude": 45.057, "Longitude": 7.583
#         },
#         "Timestamp": "2021-11-11T13:21:31.082Z",
#         "Address": null,
#         "MediaURIs": [
#             "https://safersblobstoragedev.blob.core.windows.net/reports/000010/65920fa0-7014-41a9-88e8-8a160186c6b0.jpeg"
#         ],
#         "ExtensionData": [{
#             "CategoryId": 6, "Value": "5", "Status": "unknown"
#         }],
#         "Description": "Fire report",
#         "Notes": null,
#         "Targets": null,
#         "Username": "organization.manager.test.1",
#         "OrganizationName": "Organization1",
#         "OrganizationId": 1,
#         "Source": "chatbot",
#         "IsEditable": false
#     }
# }
# """
