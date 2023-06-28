from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from drf_spectacular.utils import extend_schema_field

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


class MissionCreateSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Mission
        fields = (
            "title",
            "description",
            "start",
            "end",
            "organizationId",
            "coordinatorTeamId",
            "coordinatorPersonId",
            "source",
            "currentStatus",  # "reports",
            "duration",
            "geometry",
        )
        geo_field = "geometry"
        id_field = False

    start = serializers.DateTimeField(
        input_formats=ChatbotDateTimeFormats,
        write_only=True,
    )

    end = serializers.DateTimeField(
        input_formats=ChatbotDateTimeFormats,
        write_only=True,
    )

    organizationId = serializers.SerializerMethodField(
        method_name="get_organization_id"
    )

    coordinatorTeamId = serializers.IntegerField(
        source="coordinator_team_id", allow_null=True
    )

    coordinatorPersonId = serializers.IntegerField(
        source="coordinator_person_id", allow_null=True
    )

    currentStatus = serializers.CharField(
        source="status", default=MissionStatusChoices.CREATED
    )

    duration = serializers.SerializerMethodField()

    def get_duration(self, obj) -> dict:
        return {
            "lowerBound": obj.start,
            "upperBound": obj.end,
            "lowerBoundIsInclusive": obj.start_inclusive,
            "upperBoundIsInclusive": obj.end_inclusive,
        }

    def get_organization_id(self, obj) -> int | None:
        user = self.context["request"].user
        if user.organization:
            return int(user.organization.organization_id)
        return None

    def to_representation(self, instance):
        """
        A mission can have either a team or a person as coordinators, not both.
        Therefore, if a person is specified, ensure no team is specified
        """
        representation = super().to_representation(instance)
        coordinatorPersonId = representation["properties"].get(
            "coordinatorPersonId"
        )
        if coordinatorPersonId is not None:
            representation["properties"]["coordinatorTeamId"] = None
        return representation
