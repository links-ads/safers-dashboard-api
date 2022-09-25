from django.utils.translation import gettext_lazy as _

from rest_framework import serializers, ISO_8601
from rest_framework_gis import serializers as gis_serializers

from safers.chatbot.models import Report, ReportHazardTypes, ReportStatusTypes, ReportContentTypes, ReportVisabilityTypes

from .serializers_base import ChatbotViewSerializer


class ReportViewSerializer(ChatbotViewSerializer):
    """
    serializer to use when validating the incoming query_params for the proxy API
    (this adds a few custom fields to the default chatbot serializer)
    """

    ProxyFieldMapping = {
        **ChatbotViewSerializer.ProxyFieldMapping,
        **{
            # "hazards": "Hazards",
            # "status": "Status",
            # "content": "Contents",
            "visibility": "Visibility",
        }
    }  # yapf: disable

    hazards = serializers.MultipleChoiceField(
        choices=ReportHazardTypes.choices,
        default=[ReportHazardTypes.FIRE],
    )

    status = serializers.MultipleChoiceField(
        choices=ReportStatusTypes.choices,
        default=[
            ReportStatusTypes.UNKNOWN,
            ReportStatusTypes.NOTIFIED,
            ReportStatusTypes.MANAGED,
        ],
        required=False,
    )

    content = serializers.MultipleChoiceField(
        choices=ReportContentTypes.choices,
        required=False,
    )

    visibility = serializers.ChoiceField(
        choices=ReportVisabilityTypes.choices,
        default=ReportVisabilityTypes.ALL,
        required=False,
    )


class ReportSerializer(serializers.ModelSerializer):
    """
    serializer to use when converting the output of the proxy API to a response for the dashboard frontend
    """
    class Meta:
        model = Report
        fields = (
            "report_id",
            "name",
            "mission_id",
            "timestamp",
            "source",
            "hazard",
            "status",
            "categories",
            "categories_info",
            "content",
            "visibility",
            "description",
            "reporter",
            "media",
            "geometry",
            "location",
        )

    # id = serializers.CharField(source="report_id")

    geometry = gis_serializers.GeometryField(
        precision=Report.PRECISION, remove_duplicates=True
    )

    location = serializers.SerializerMethodField()

    categories = serializers.SerializerMethodField()
    categories_info = serializers.SerializerMethodField()

    def get_location(self, obj):
        if obj.geometry:
            return obj.geometry.coords

    def get_categories(self, obj):
        # only returning the category_group
        categories_groups = [category["group"] for category in obj.categories]
        return set(categories_groups)

    def get_categories_info(self, obj):
        categories_info = []
        for category in obj.categories:
            name = category["name"]
            value = category["value"]
            units = category["units"]
            category_info_string = ""
            if name:
                category_info_string += f" {name}:"
            if value:
                category_info_string += f" {value}"
                if units and units != "units":
                    category_info_string += f" {units}"
            if category_info_string:
                categories_info.append(category_info_string.strip())

        return categories_info

    def create(self):
        """
        creates a model instance w/out saving it
        """
        return Report(**self.validated_data)
