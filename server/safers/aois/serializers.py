from collections import OrderedDict

from django.contrib.gis.geos import Point

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.core.fields import SimplifiedGeometryField

from safers.aois.models import Aoi


class AoiSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Aoi
        fields = (
            "id",
            "name",
            "description",
            "country",
            "zoom_level",
            "midpoint",
            "geometry",
        )
        id_field = False
        geo_field = "geometry"
        list_serializer_class = serializers.ListSerializer  # don't combine multiple AOIs into a FeatureCollection

    geometry = gis_serializers.GeometryField(
        precision=Aoi.PRECISION, remove_duplicates=True
    )

    midpoint = SimplifiedGeometryField(
        precision=Aoi.PRECISION, geometry_class=Point
    )

    def to_representation(self, data):
        """
        Output a single AOI as a FeatureCollection, even though there is only one Feature
        """
        representation = super().to_representation(data)
        return OrderedDict((
            ("type", "FeatureCollection"),
            ("features", [representation]),
        ))

    def to_internal_value(self, data):
        """
        Extracts the single feature from the FeatureCollection
        """

        feature = data["features"][0]
        return super().to_internal_value(feature)
