from django.conf import settings
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake
from safers.core.views import CannotDeleteViewSet

from safers.events.models import Event, EventStatus
from safers.events.serializers import EventSerializer

_event_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": "9953b183-5f18-41b1-ac96-23121ac33de7",
        "timestamp": "2022-03-19T10:01:04Z",
        "description": "string",
        "source": "string",
        "status": "UNVALIDATED",
        "media": [
            "http://some.image.com",
            "http://another.image.com"
        ],
        "geometry": {
            "type": "Polygon",
            "coordinates": [[1,2],[3,4]]
        },
        "bounding_box": {
            "type": "Polygon",
            "coordinates": [[1,2],[3,4]]
        }
    }
)  # yapf: disable

_event_list_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY, items=_event_schema
)


# @method_decorator(
#     swagger_auto_schema(responses={status.HTTP_200_OK: _alert_list_schema}),
#     name="list",
# )
# @method_decorator(
#     swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
#     name="create",
# )
# @method_decorator(
#     swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
#     name="retrieve",
# )
# @method_decorator(
#     swagger_auto_schema(responses={status.HTTP_200_OK: _alert_schema}),
#     name="update",
# )
class EventViewSet(CannotDeleteViewSet):
    # permission_classes = [TODO: SOME KIND OF FACTORY FUNCTION HERE]
    serializer_class = EventSerializer
    lookup_field = "id"
    lookup_url_kwarg = "event_id"

    @swagger_fake(Event.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE ALERTS THIS USER CAN ACCESS
        return Event.objects.all()

    # TODO: NOT SURE IF I SHOULD HAVE A SEPARATE ACTION HERE
    # TODO: OR JUST USE A PUT REQUEST TO THE USERS API
    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        user = request.user
        event = self.get_object()

        max_favorite_events = settings.SAFERS_MAX_FAVORITE_EVENTS
        if user.favorite_events.count() >= max_favorite_events:
            return Response(
                data={
                    "error":
                        f"{user} cannot have more than {max_favorite_events} events."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        user.favorite_events.add(event)

        return Response(
            data={"detail": f"{user} favorited {event}."},
            status=status.HTTP_200_SUCCESS,
        )
