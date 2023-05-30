from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

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

    def get_center(self, obj):
        coords = obj.center.coords
        return map(lambda x: round(x, Notification.PRECISION), coords)

    def get_bounding_box(self, obj):
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
