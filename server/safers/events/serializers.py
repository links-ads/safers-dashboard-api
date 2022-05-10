from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.alerts.models import Alert

from safers.events.models import Event, EventStatus


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "id",
            "description",
            "start_date",
            "end_date",
            "people_affected",
            "causalties",
            "estimated_damage",
            "alerts",
            "status",
            "geometry",
            "bounding_box",
            "center",
            "favorite",
            "alerts",
        )

    geometry = gis_serializers.GeometryField(
        precision=Event.PRECISION,
        read_only=True,
        remove_duplicates=True,
        source="geometry_collection",
    )
    center = serializers.SerializerMethodField()
    bounding_box = serializers.SerializerMethodField()

    status = serializers.SerializerMethodField()

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    alerts = serializers.SlugRelatedField(
        many=True, slug_field="id", queryset=Alert.objects.all()
    )

    def get_center(self, obj):
        coords = obj.center.coords
        return map(lambda x: round(x, Event.PRECISION), coords)

    def get_bounding_box(self, obj):
        coords = obj.bounding_box.extent
        return map(lambda x: round(x, Event.PRECISION), coords)

    def get_status(self, obj):
        if obj.closed:
            return EventStatus.CLOSED
        elif obj.open:
            return EventStatus.OPEN

    def is_favorite(self, obj):
        user = self.context["request"].user
        return obj in user.favorite_events.all()
