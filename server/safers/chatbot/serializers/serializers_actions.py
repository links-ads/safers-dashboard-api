from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from drf_spectacular.utils import extend_schema_field

from safers.chatbot.models import Action, ActionStatusTypes
from .serializers_base import ChatbotViewSerializer


class ActionViewSerializer(ChatbotViewSerializer):
    """
    serializer to use when validating the incoming query_params for the proxy API
    (this adds a few custom fields to the default chatbot serializer)
    """
    ProxyFieldMapping = {
        **ChatbotViewSerializer.ProxyFieldMapping,
        **{
            "status": "StatusTypes"
        }
    }  # yapf:disable

    status = serializers.MultipleChoiceField(
        choices=ActionStatusTypes.choices,
        required=False,
    )

    # TODO: ActivityIds


class ActionSerializer(serializers.ModelSerializer):
    """
    serializer to use when converting the output of the proxy API to a response for the dashboard frontend
    """
    class Meta:
        model = Action
        fields = (
            "id",
            "activity",
            "name",
            "username",
            "organization",
            "status",
            "source",
            "timestamp",
            "geometry",
            "location",
        )

    id = serializers.CharField(source="action_id")

    geometry = gis_serializers.GeometryField(
        precision=Action.PRECISION, remove_duplicates=True
    )

    location = serializers.SerializerMethodField()

    @extend_schema_field({
        "type": "object",
        "example": {
            "longitude": 12.9721,
            "latitude": 77.5933,
        }
    })
    def get_location(self, obj):
        if obj.geometry:
            return obj.geometry.coords

    def validate(self, data):

        validated_data = super().validate(data)

        # if activity has a value, status must be "Active"...
        activity = validated_data.get("activity")
        status = validated_data.get("status")
        if activity and status != ActionStatusTypes.ACTIVE:
            raise serializers.ValidationError(
                "Only 'active' actions can have an activity."
            )

        return validated_data
