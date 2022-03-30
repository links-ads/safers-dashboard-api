from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.chatbot.models import Report


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            "id",
            "external_id",

            "geometry",
            "bounding_box",
        )  # yapf: disable

    geometry = gis_serializers.GeometryField(
        precision=Report.PRECISION, remove_duplicates=True
    )
    bounding_box = gis_serializers.GeometryField(precision=Report.PRECISION)
