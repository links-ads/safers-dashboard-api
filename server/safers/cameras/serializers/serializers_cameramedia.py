from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.cameras.models import Camera, CameraMedia, CameraMediaFireClass, CameraMediaTag


class CameraMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraMedia
        fields = (
            "id",
            "timestamp",
            "description",
            "camera_id",
            "type",
            "fire_classes",
            "tags",
            "direction",
            "distance",
            "geometry",
            "url",
            "favorite",
        )

    camera_id = serializers.SlugRelatedField(
        slug_field="camera_id", queryset=Camera.objects.all(), source="camera"
    )
    fire_classes = serializers.SlugRelatedField(
        slug_field="name",
        queryset=CameraMediaFireClass.objects.all(),
        many=True
    )

    tags = serializers.SlugRelatedField(
        slug_field="name", queryset=CameraMediaTag.objects.all(), many=True
    )

    geometry = gis_serializers.GeometryField(
        precision=CameraMedia.PRECISION, allow_null=True, required=False
    )

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    def is_favorite(self, obj):
        user = self.context["request"].user
        return obj in user.favorite_camera_medias.all()
