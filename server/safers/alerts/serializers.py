from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = (
            "id",
            "timestamp",
            "description",
            "source",
            "status",
            "media",
            "geometry",
            "bounding_box",
        )
        # extra_kwargs = {
        #     # many fields should be read-only ?
        #     field: dict([("read_only", True)])
        #     for field in ["timestamp", "source", "media", "geometry", "bounding_box"]
        # }  # yapf: disable

    geometry = gis_serializers.GeometryField(
        precision=Alert.PRECISION, remove_duplicates=True
    )
    bounding_box = gis_serializers.GeometryField(precision=Alert.PRECISION)
