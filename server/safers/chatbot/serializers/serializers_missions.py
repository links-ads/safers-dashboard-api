from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.chatbot.models import Mission, MissionStatusTypes
from .serializers_base import ChatbotViewSerializer


class MissionViewSerializer(ChatbotViewSerializer):
    """
    serializer to use when validating the incoming query_params for the proxy API
    (this adds a few custom fields to the default chatbot serializer)
    """
    ProxyFieldMapping = {
        **ChatbotViewSerializer.ProxyFieldMapping,
        **{
            "status": "Status"
        }
    }  # yapf:disable

    status = serializers.MultipleChoiceField(
        choices=MissionStatusTypes.choices,
        required=False,
    )

    # TODO: ActivityIds


class MissionSerializer(serializers.ModelSerializer):
    """
    serializer to use when converting the output of the proxy API to a response for the dashboard frontend
    """
    class Meta:
        model = Mission
        fields = (
            "id",
            "name",
            "description",
            "username",
            "organization",
            "start",
            "end",
            "status",
            "source",
            "reports",
            "geometry",
            "location",
        )

    id = serializers.CharField(source="mission_id")

    geometry = gis_serializers.GeometryField(
        precision=Mission.PRECISION, remove_duplicates=True
    )

    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        if obj.geometry:
            return obj.geometry.coords
