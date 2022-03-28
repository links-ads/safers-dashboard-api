from django.utils import timezone

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.tasks.models import Message, MessageBody
from safers.tasks.constants import MESSAGE_USER_ID, MESSAGE_DELIVERY_MODE


class MessageBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageBody
        fields = ("datatype_id", )


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "message_id",
            "app_id",
            "user_id",
            "delivery_mode",
            "timestamp",
            "body",
        )

    body = MessageBodySerializer()

    # message_id = serializers.CharField()
    # app_id = serializers.CharField()
    # user_id = serializers.SerializerMethodField()
    # delivery_mode = serializers.SerializerMethodField()
    # timestamp = serializers.DateTimeField(default=timezone.now)

    # payload = serializers.JSONField(required=False)

    # def get_user_id(self, obj):
    #     return MESSAGE_USER_ID

    # def get_delivery_mode(self, obj):
    #     return MESSAGE_DELIVERY_MODE
