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
    SURVEILLANCE = "Surveillance", _("Surveillance"),
    OPERATIVE_CENTER = "In activity in operative centers", _("In activity in operative centers"),
    AIB_MODULES = "AIB Modules", _("AIB Modules"),
    MOBILE_TUBS = "Mobile tubs", _("Mobile tubs"),
    POWERED_EQUIPMENT = "Powered equip.", _("Powered equip."),
    MANUAL_EQUIPMENT = "Manual equip.", _("Manual equip."),
    PUMPING_EQUIPMENT = "Pumping equip.", _("Pumping equip."),
    BARRIERS = "Barriers", _("Barriers"),
    OPERATIVE_MACHINES = "Operative machines", _("Operative machines"),
    ASSISTANCE = "Assistance to the population", _("Assistance to the population"),
    FIRE_EXTINGUISHER_SYSTEM = "Fire ext. system", _("Fire ext. system"),
    FUEL_REDUCTION = "Fuel reduction", _("Fuel reduction"),
    FIRE_SUPPRESSION = "Fire suppression", _("Fire suppression"),
    IMPACT_ASSESSMENT = "Impact assessment", _("Impact assessment"),
    RESTORATION = "Restoration", _("Restoration"),
    EVACUATION = "Evacuation", _("Evacuation"),
    SEARCH_AND_RESCUE = "Search and rescue", _("Search and rescue"),
    RUBBLE_REMOVAL = "Rubble removal", _("Rubble removal"),
    SEARCH_MISSING = "Search missing", _("Search missing"),


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
