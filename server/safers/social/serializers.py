from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.social.models import SocialEvent


class SocialEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialEvent
        fields = (
            "id",
            "external_id",
            "category",
            "severity",
            "start_date",
            "end_date",
            "geometry",
            "bounding_box",
        )  # yapf: disable

    geometry = gis_serializers.GeometryField(
        precision=SocialEvent.PRECISION, remove_duplicates=True
    )
    bounding_box = gis_serializers.GeometryField(
        precision=SocialEvent.PRECISION
    )
