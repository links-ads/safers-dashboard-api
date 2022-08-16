from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ActionSourceTypes(models.TextChoices):
    CHATBOT = "Chatbot", _("Chatbot"),


class ActionStatusTypes(models.TextChoices):
    OFF = "Off", _("Off")
    READY = "Ready", _("Ready")
    MOVING = "Moving", _("Moving")
    ACTIVE = "Active", _("Active")


class ActionActivityTypes(models.TextChoices):
    pass


class Action(gis_models.Model):
    class Meta:
        verbose_name = "Action"
        verbose_name_plural = "Actions"

    PRECISION = 12

    action_id = models.CharField(
        max_length=128, unique=True, blank=False, null=False
    )

    timestamp = models.DateTimeField(blank=True, null=True)

    username = models.CharField(max_length=128, blank=True, null=True)
    organization = models.CharField(max_length=128, blank=True, null=True)
    activity = models.CharField(
        max_length=128,
        choices=ActionActivityTypes.choices,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=64,
        choices=ActionStatusTypes.choices,
        blank=True,
        null=True,
    )
    source = models.CharField(
        max_length=64,
        choices=ActionSourceTypes.choices,
        default=ActionSourceTypes.CHATBOT,
    )
    geometry = gis_models.GeometryField(blank=False, null=False)

    @property
    def name(self):
        return f"Action {self.action_id}"

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "Action is not stored in the db and therefore cannot be saved."
        )
