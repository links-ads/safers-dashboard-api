from collections import OrderedDict

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.cameras.models import Camera


class CameraDetailSerializer(serializers.ModelSerializer):
    """
    return JSON
    """
    class Meta:
        model = Camera
        fields = (
            "id",
            "description",
            "direction",
            "altitude",
            "location",
            "geometry",
            "last_update",
        )

    id = serializers.CharField(
        source="camera_id"
    )  # note this is the external camera_id rather than the internal id

    geometry = gis_serializers.GeometryField(
        precision=Camera.PRECISION, remove_duplicates=True
    )

    location = serializers.SerializerMethodField()

    description = serializers.SerializerMethodField()

    def get_location(self, obj):
        if obj.geometry:
            longitude, latitude = obj.geometry.coords
            return {
                "longitude": longitude,
                "latitude": latitude,
            }

    def get_description(self, obj):
        descriptors = OrderedDict((
            ("name", obj.name),
            ("model", obj.model),
            ("owner", obj.owner),
            ("nation", obj.nation),
        ))
        return ", ".join([
            f"{k}: {v}" for k, v in descriptors.items() if v is not None
        ])


class CameraListSerializer(
    gis_serializers.GeoFeatureModelSerializer, CameraDetailSerializer
):
    """
    returns GeoJSON 
    """
    class Meta:
        model = Camera
        fields = (
            "id",
            "description",
            "direction",
            "altitude",
            "location",
            "geometry",
            "last_update",
        )
        id_field = None
        geo_field = "geometry"
