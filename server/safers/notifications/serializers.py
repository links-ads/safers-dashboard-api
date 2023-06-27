from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from drf_spectacular.utils import extend_schema_field

from safers.notifications.models import Notification, NotificationGeometry


class NotificationGeometrySerializer(gis_serializers.GeoFeatureModelSerializer):
    class Meta:
        model = NotificationGeometry
        fields = (
            "description",
            "geometry",
        )
        geo_field = "geometry"
        id_field = False


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "title",
            "type",
            "timestamp",
            "status",
            "source",
            "scope",
            "restriction",
            "scopeRestriction",
            "target_organizations",
            "category",
            "event",
            "description",
            "country",
            "geometry",
            "center",
            "bounding_box",
            "message",
        )

    scopeRestriction = serializers.CharField(
        source="scope_restriction", read_only=True
    )
    target_organizations = serializers.ListField(
        source="target_organization_ids"
    )
    geometry = NotificationGeometrySerializer(many=True, source="geometries")
    center = serializers.SerializerMethodField()
    bounding_box = serializers.SerializerMethodField()
    message = serializers.JSONField(write_only=True)

    @extend_schema_field({"type": "object", "example": [12.9721, 77.5933]})
    def get_center(self, obj) -> list:
        coords = obj.center.coords
        return map(lambda x: round(x, Notification.PRECISION), coords)

    @extend_schema_field({
        "type": "object", "example": [12.97, 77.59, 13.00, 78.00]
    })
    def get_bounding_box(self, obj) -> list:
        coords = obj.bounding_box.extent
        return map(lambda x: round(x, Notification.PRECISION), coords)

    def create(self, validated_data):
        geometries_data = validated_data.pop("geometries", {})
        notification = super().create(validated_data)
        for geometry_data in geometries_data:
            notification_geometry = NotificationGeometry(
                **geometry_data, notification=notification
            )
            notification_geometry.save()
        return notification
