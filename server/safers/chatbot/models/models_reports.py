import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _

from safers.core.models import Country
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
            "organization": {"type": ["string", "null"]}
        },
    }  # yapf: disable

    return validate_schema(value, reporter_schema)


def validate_categories(value):
    """
    A simple validator that ensures report.categories is a correctly-formatted object
    """

    categories_schema = {
        "type": "array",
        "items": [{
            "type": "object",
            "properties": {
                "group": {"type": "string"},
                "sub_group": {"type": "string"},
                "name": {"type": "string"},
                "units": {"type": "string"},
                "value": {"type": "string"},
                "status": {"type": "string"},
            }
        }]
    }  # yapf: disable

    return validate_schema(value, categories_schema)


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

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )  # TODO: figure out how to remove this field w/out generating 'ProgrammingError: cannot cast type uuid to bigint'

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
    categories = models.JSONField(
        validators=[validate_categories], default=list
    )
    geometry = gis_models.GeometryField(blank=False, null=False)

    def __str__(self):
        return f"{self.report_id}"

    @property
    def name(self):

        if self.reporter.get("organization"):
            report_scope = "PRO"  # user has organization => professional report
        else:
            report_scope = "CIT"  # user has no organization => citizen report

        serial_number = f"S{self.report_id:0>5}"

        country = Country.objects.filter(geometry__intersects=self.geometry
                                        ).first()

        return "-".join(
            filter(
                None,
                map(
                    str,
                    [
                        "REP",
                        report_scope,
                        self.timestamp.year,
                        serial_number,
                        country.admin_code if country else None,
                    ]
                )
            )
        )

    @property
    def visibility(self):
        if self.is_public:
            return ReportVisabilityTypes.PUBLIC
        return ReportVisabilityTypes.PRIVATE

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "Report is not stored in the db and therefore cannot be saved."
        )


class ReportCategory(models.Model):
    class Meta:
        verbose_name = "Report Category"
        verbose_name_plural = "Report Categories"
        ordering = ("category_id", )

    category_id = models.IntegerField(blank=False, null=False, unique=True)

    type = models.CharField(max_length=128, blank=True, null=True)
    hazard = models.CharField(max_length=128, blank=True, null=True)
    target_key = models.CharField(max_length=128, blank=True, null=True)
    target = models.CharField(max_length=128, blank=True, null=True)
    group = models.CharField(max_length=128, blank=True, null=True)
    group_key = models.CharField(max_length=128, blank=True, null=True)
    sub_group = models.CharField(max_length=128, blank=True, null=True)
    sub_group_key = models.CharField(max_length=128, blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    code = models.CharField(max_length=128, blank=True, null=True)
    group_code = models.CharField(max_length=128, blank=True, null=True)
    unit_of_measure = models.CharField(max_length=128, blank=True, null=True)
    min_value = models.CharField(max_length=128, blank=True, null=True)
    max_value = models.CharField(max_length=128, blank=True, null=True)
    values = ArrayField(
        models.CharField(max_length=128), blank=True, default=list
    )

    # groupIcon = models.CharField(blank=True, null=True)
    # fieldType = models.CharField(blank=True, null=True)


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
