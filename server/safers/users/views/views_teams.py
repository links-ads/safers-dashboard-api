from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiTypes

from safers.core.authentication import TokenAuthentication
from safers.core.clients import GATEWAY_CLIENT

_teams_view_response = OpenApiResponse(
    OpenApiTypes.ANY,
    examples=[
        OpenApiExample(
            "professional response",
            [{
                "id": 123,
                "name": "team1",
                "members": [{
                    "id": 456,
                    "name": "user1",
                }]
            }]
        ),
        OpenApiExample("citizen response", [None]),
    ]
)


@extend_schema(responses={
    status.HTTP_200_OK: _teams_view_response,
})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teams_view(request):
    """
    Returns a summary of teams for the current user
    """
    user = request.user
    if user.is_professional:
        teams_data = GATEWAY_CLIENT.get_teams(
            auth=TokenAuthentication(request.auth),
        )["data"]
    else:
        teams_data = []

    teams = [
        {
            "id": team["id"],
            "name": team["name"],
            "members": [
                {
                    "id": member["id"],
                    "name": member["displayName"],
                }
                for member in team["members"]
            ]
        }
        for team in teams_data
    ]  # yapf: disable

    return Response(teams, status=status.HTTP_200_OK)
