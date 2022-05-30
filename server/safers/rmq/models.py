import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class MessageStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")


class MessageManager(models.Manager):
    pass


class MessageQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=MessageStatus.PENDING)

    def demo(self):
        return self.filter(is_demo=True)


class Message(models.Model):
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    objects = MessageManager.from_queryset(MessageQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text=_(
            "Provides a way to identify messages in order to re-use them for demos, etc."
        ),
    )
    is_demo = models.BooleanField(
        default=False,
        help_text=_("Identifies messages that should be used for demos, etc."),
    )

    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text=_(
            "This is the timestamp that the message was sent, "
            "NOT the timestamp of the artefact being messaged about "
            "(that is likely to be found in the message body)."
        )
    )

    status = models.CharField(
        max_length=64,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING,
        blank=True,
        null=True,
    )

    routing_key = models.CharField(
        max_length=255, blank=False, null=False, default=str
    )

    body = models.JSONField(default=dict)
