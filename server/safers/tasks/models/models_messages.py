from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone

from safers.tasks.constants import MESSAGE_USER_ID, MESSAGE_DELIVERY_MODE

# not planning on saving these messages, but defining them as models helps w/ serializers


class Message(models.Model):

    message_id = models.CharField(max_length=128)
    app_id = models.CharField(max_length=128)
    user_id = models.CharField(max_length=128)
    delivery_mode = models.CharField(
        max_length=128, default=MESSAGE_DELIVERY_MODE
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message_id


class MessageBody(gis_models.Model):

    datatype_id = models.IntegerField()

    message = models.OneToOneField(
        Message, on_delete=models.CASCADE, related_name="body"
    )
