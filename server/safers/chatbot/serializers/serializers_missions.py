import json

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.core.fields import UnderspecifiedDateTimeField

from safers.chatbot.models import Mission, MissionStatusChoices
from .serializers_base import ChatbotViewSerializer, ChatbotDateTimeFormats


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
        choices=MissionStatusChoices.choices,
        required=False,
    )


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

    start = serializers.DateTimeField(input_formats=ChatbotDateTimeFormats)
    end = serializers.DateTimeField(input_formats=ChatbotDateTimeFormats)

    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        if obj.geometry:
            return obj.geometry.coords


class MissionCreateSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Mission
        fields = (
            "title",
            "description",
            "start",
            "end",
            "organizationId",
            "source",
            "currentStatus",  # "reports",
            "duration",
            "geometry",
        )
        geo_field = "geometry"
        id_field = False

    start = UnderspecifiedDateTimeField(
        input_formats=ChatbotDateTimeFormats,
        write_only=True,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = UnderspecifiedDateTimeField(
        input_formats=ChatbotDateTimeFormats,
        write_only=True,
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )

    organizationId = serializers.SerializerMethodField(
        method_name="get_organization_id"
    )

    currentStatus = serializers.CharField(
        source="status", default=MissionStatusChoices.CREATED
    )

    duration = serializers.SerializerMethodField()

    def get_duration(self, obj):
        return {
            "lowerBound": obj.start,
            "upperBound": obj.end,
            "lowerBoundIsInclusive": obj.start_inclusive,
            "upperBoundIsInclusive": obj.end_inclusive,
        }

    def get_organization_id(self, obj):
        user = self.context["request"].user
        if user.organization:
            return user.organization.organization_id
        return None
