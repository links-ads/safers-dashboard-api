from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.chatbot.models import Action
from .serializers_base import ChatbotViewSerializer


class ActionViewSerializer(ChatbotViewSerializer):
    """
    serializer to use when validating the incoming query_params for the proxy API
    """
    pass

    # TODO: StatusTypes
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

    def get_location(self, obj):
        if obj.geometry:
            return obj.geometry.coords
