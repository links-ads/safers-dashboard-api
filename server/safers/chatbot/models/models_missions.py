from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from safers.core.utils import validate_schema


def validate_reports(value):
    """
    A simple validator that ensures mission.reports is a list of correctly-formatted objects
    """

    reports_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "id": {"type": "string"}
            },
            "required": ["name", "id"],
        }
    }  # yapf: disable

    return validate_schema(value, reports_schema)


class MissionSourceTypes(models.TextChoices):
    CHATBOT = "Chatbot", _("Chatbot"),


class MissionStatusTypes(models.TextChoices):
    CREATED = "Created", _("Created")
    TAKEN_IN_CHARGE = "TakenInCharge", _("Taken In Charge")
    COMPLETED = "Completed", _("Completed")
    DELETED = "Deleted", _("Deleted")


class Mission(gis_models.Model):
    class Meta:
        verbose_name = "Mission"
        verbose_name_plural = "Missions"

    PRECISION = 12

    mission_id = models.CharField(
        max_length=128, unique=True, blank=False, null=False
    )

    username = models.CharField(max_length=128, blank=True, null=True)
    organization = models.CharField(max_length=128, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start = models.DateTimeField()
    start_inclusive = models.BooleanField()
    end = models.DateTimeField()
    end_inclusive = models.BooleanField()
    source = models.CharField(
        max_length=64,
        choices=MissionSourceTypes.choices,
        default=MissionSourceTypes.CHATBOT,
    )
    status = models.CharField(
        max_length=64,
        choices=MissionStatusTypes.choices,
        blank=True,
        null=True,
    )
    reports = models.JSONField(
        blank=True,
        default=dict,
        validators=[validate_reports],
    )
    geometry = gis_models.GeometryField(blank=False, null=False)

    @property
    def name(self):
        return f"Mission {self.mission_id}"

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "Action is not stored in the db and therefore cannot be saved."
        )
