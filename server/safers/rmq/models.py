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

    timestamp = models.DateTimeField(default=timezone.now)

    status = models.CharField(
        max_length=64,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING,
        blank=True,
        null=True,
    )

    routing_key = models.CharField(
        max_length=255, blank=False, null=False, default=dict
    )

    body = models.JSONField()
