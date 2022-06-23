from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.rmq.models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = (
            "id",
            "timestamp",
            "routing_key",
            "status",
            "body",
        )
