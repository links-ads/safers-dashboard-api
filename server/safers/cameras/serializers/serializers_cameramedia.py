from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.cameras.models import Camera, CameraMedia, CameraMediaFireClass


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
            "is_fire",
            "is_smoke",
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

    tags = serializers.SerializerMethodField()

    geometry = gis_serializers.GeometryField(
        precision=CameraMedia.PRECISION, allow_null=True, required=False
    )

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    def get_tags(self, obj):
        tags = []
        if obj.is_smoke:
            tags.append("smoke")
        if obj.is_fire:
            tags.append("fire")
        return tags

    def is_favorite(self, obj):
        return "foo"
        user = self.context["request"].user
        return obj in user.favorite_camera_medias.all()
