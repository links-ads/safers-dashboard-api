from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

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
            "favorite",
        )

    geometry = gis_serializers.GeometryField(
        precision=Event.PRECISION, remove_duplicates=True
    )
    bounding_box = gis_serializers.GeometryField(precision=Event.PRECISION)

    status = serializers.SerializerMethodField()

    favorite = serializers.SerializerMethodField(method_name="is_favorite")

    def get_status(self, obj):
        if obj.closed:
            return EventStatus.CLOSED
        elif obj.open:
            return EventStatus.OPEN

    def is_favorite(self, obj):
        user = self.context["request"].user
        return obj in user.favorite_events.all()