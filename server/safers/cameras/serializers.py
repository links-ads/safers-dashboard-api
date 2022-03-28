from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.cameras.models import Camera, CameraMedia, CameraMediaTag


class CameraSerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = Camera
        fields = (
            "id",
            "name",
            "description",
            "last_update",
            "geometry",
        )
        id_field = "id"
        geo_field = "geometry"

    geometry = gis_serializers.GeometryField(
        precision=Camera.PRECISION, remove_duplicates=True
    )


class CameraMediaTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraMediaTag
        fields = ("name", )


class CameraMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraMedia
        fields = (
            "id",
            "hash",
            "timestamp",
            "description",
            "camera",
            "smoke_column_class",
            "geographical_direction",
            "type",
            "tags",
            "geometry",
            "bounding_box",
            "favorite",
        )

    tags = serializers.SlugRelatedField(
        slug_field="name", queryset=CameraMediaTag.objects.all(), many=True
    )

    geometry = gis_serializers.GeometryField(
        precision=CameraMedia.PRECISION, remove_duplicates=True
    )
    bounding_box = gis_serializers.GeometryField(
        precision=CameraMedia.PRECISION
    )

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    def is_favorite(self, obj):
        user = self.context["request"].user
        return obj in user.favorite_camera_medias.all()

    # TODO: WRITEABLE NESTED SERIALIZER
    # def create(self, validated_data):
    #     pass
