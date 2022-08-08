from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.chatbot.models import Communication
from .serializers_base import ChatbotViewSerializer


class CommunicationViewSerializer(ChatbotViewSerializer):
    """
    serializer to use when validating the incoming query_params for the proxy API
    """
    pass


class CommunicationSerializer(serializers.ModelSerializer):
    """
    serializer to use when converting the output of the proxy API to a response for the dashboard frontend
    """
    class Meta:
        model = Communication
        fields = (
            "id",
            "name",
            "status",
            "target",
            "start",
            "end",
            "source",
            "message",
            "geometry",
            "location",
        )

    id = serializers.CharField(source="communication_id")

    geometry = gis_serializers.GeometryField(
        precision=Communication.PRECISION, remove_duplicates=True
    )

    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        if obj.geometry:
            return obj.geometry.coords
