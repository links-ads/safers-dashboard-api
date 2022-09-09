from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from safers.core.utils import validate_schema


def validate_assigned_to(value):
    """
    A simple validator that ensures communication.assigned_to is a list of strings
    """

    assigned_to_schema = {
        "type": "array",
        "items": {
            "type": "string",
        },
    }

    return validate_schema(value, assigned_to_schema)


class CommunicationSourceTypes(models.TextChoices):
    CHATBOT = "Chatbot", _("Chatbot"),


class CommunicationStatusTypes(models.TextChoices):
    ONGOING = "Ongoing", _("Ongoing"),
    EXPIRED = "Expired", _("Expired"),


class CommunicationScopeTypes(models.TextChoices):
    PUBLIC = "Public", _("Public"),
    RESTRICTED = "Restricted", _("Restricted"),


class CommunicationRestrictionTypes(models.TextChoices):
    CITIZEN = "Citizen", _("Citizen"),
    PROFESSIONAL = "Professional", _("Professional"),
    ORGANIZATION = "Organization", _("Organization"),
    NONE = "None", _("None"),


class Communication(gis_models.Model):
    class Meta:
        verbose_name = "Communication"
        verbose_name_plural = "Communications"

    PRECISION = 12

    communication_id = models.CharField(
        max_length=128, unique=True, blank=False, null=False
    )

    source_organization = models.ForeignKey(
        "users.organization",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="chatbot_communications"
    )

    start = models.DateTimeField()
    start_inclusive = models.BooleanField(default=True)
    end = models.DateTimeField()
    end_inclusive = models.BooleanField(default=True)

    source = models.CharField(
        max_length=64,
        choices=CommunicationSourceTypes.choices,
        default=CommunicationSourceTypes.CHATBOT,
    )

    scope = models.CharField(
        max_length=64,
        choices=CommunicationScopeTypes.choices,
        default=CommunicationScopeTypes.PUBLIC,
    )
    restriction = models.CharField(
        max_length=64,
        choices=CommunicationRestrictionTypes.choices,
        default=CommunicationRestrictionTypes.NONE,
    )
    target_organizations = models.ManyToManyField(
        "users.organization",
        related_name="targeted_chatbot_communications",
    )

    assigned_to = models.JSONField(
        validators=[validate_assigned_to],
        default=list,
        # TODO: SHOULD REALLY BE USING target_organization FOR THIS, BUT HAVE TO WAIT
        # TODO: UNTIL I'VE LINKED FusionAuth Organization w/ Django Organizations
    )

    message = models.TextField(blank=True, null=True)

    geometry = gis_models.GeometryField(blank=False, null=False)

    @property
    def name(self):
        return f"Communication {self.communication_id}"

    @property
    def status(self):
        now = timezone.now().date()
        end = self.end.date()
        if self.end_inclusive and end >= now:
            return CommunicationStatusTypes.ONGOING
        elif (not self.end_inclusive) and end > now:
            return CommunicationStatusTypes.ONGOING
        else:
            return CommunicationStatusTypes.EXPIRED

    @property
    def target(self):
        if self.scope == CommunicationScopeTypes.PUBLIC:
            return self.scope
        elif self.scope == CommunicationScopeTypes.RESTRICTED:
            return self.restriction

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "Communication is not stored in the db and therefore cannot be saved."
        )
