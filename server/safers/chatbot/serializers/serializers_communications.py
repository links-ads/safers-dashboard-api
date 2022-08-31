from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.chatbot.models import Communication
from .serializers_base import ChatbotViewSerializer, ChatbotDateTimeFormats


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
            "assigned_to",
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


class CommunicationCreateSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Communication
        fields = (
            "message",
            "start",
            "end",
            "organizationIdList",
            "scope",
            "restriction",
            "duration",
            "geometry",
        )
        geo_field = "geometry"
        id_field = False

    start = serializers.DateTimeField(
        input_formats=ChatbotDateTimeFormats, write_only=True
    )
    end = serializers.DateTimeField(
        input_formats=ChatbotDateTimeFormats, write_only=True
    )

    organizationIdList = serializers.SerializerMethodField(
        method_name="get_organization_id_list"
    )

    duration = serializers.SerializerMethodField()

    def get_duration(self, obj):
        return {
            "lowerBound": obj.start,
            "upperBound": obj.end,
            "lowerBoundIsInclusive": obj.start_inclusive,
            "upperBoundIsInclusive": obj.end_inclusive,
        }

    def get_organization_id_list(self, obj):
        user = self.context["request"].user
        if user.organization:
            return [user.organization.organization_id]
        return []
