from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from safers.core.utils import validate_schema, SpaceInsensitiveTextChoices


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


class MissionSourceChoices(models.TextChoices):
    CHATBOT = "Chatbot", _("Chatbot"),


class MissionStatusChoices(SpaceInsensitiveTextChoices):
    CREATED = "Created", _("Created")
    TAKEN_IN_CHARGE = "Taken In Charge", _("Taken In Charge")
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

    title = models.CharField(max_length=128, blank=True, null=True)
    username = models.CharField(max_length=128, blank=True, null=True)
    organization = models.CharField(max_length=128, blank=True, null=True)
    coordinator_team_id = models.IntegerField(blank=True, null=True)
    coordinator_person_id = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    start = models.DateTimeField()
    start_inclusive = models.BooleanField(default=True)
    end = models.DateTimeField()
    end_inclusive = models.BooleanField(default=True)
    source = models.CharField(
        max_length=64,
        choices=MissionSourceChoices.choices,
        default=MissionSourceChoices.CHATBOT,
    )
    status = models.CharField(
        max_length=64,
        choices=MissionStatusChoices.choices,
        default=MissionStatusChoices.CREATED,
    )
    reports = models.JSONField(
        blank=True,
        default=dict,
        validators=[validate_reports],
    )
    geometry = gis_models.GeometryField(blank=False, null=False)

    @property
    def name(self) -> str:
        return self.title or f"Mission {self.mission_id}"

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "Action is not stored in the db and therefore cannot be saved."
        )
