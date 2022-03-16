from rest_framework import serializers
# from rest_framework_gis.serializers import GeometryField
from rest_framework_gis import serializers as gis_serializers

from safers.aois.models import Aoi


class AoiSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Aoi
        fields = (
            "id",
            "name",
            "description",
            "geometry",
        )
        id_field = "id"
        geo_field = "geometry"
        list_serializer_class = serializers.ListSerializer  # don't combine models into a single FeatureCollection

    geometry = gis_serializers.GeometryField(
        precision=Aoi.PRECISION,
        remove_duplicates=True,
        read_only=True,
    )
