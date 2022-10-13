import requests
from urllib.parse import urljoin

from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.users.authentication import ProxyAuthentication

_team_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "id": 123,
        "name": "team1",
        "members": [{
            "id": 456,
            "name": "user1",
        }]
    }
)  # yapf: disable

_team_list_schema = openapi.Schema(type=openapi.TYPE_ARRAY, items=_team_schema)


@swagger_auto_schema(
    responses={status.HTTP_200_OK: _team_list_schema}, method="get"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def teams_view(request):
    """
    Returns a summary of teams for the current user
    """

    GET_TEAMS_URL_PATH = "/api/services/app/Teams/GetTeams"

    user = request.user

    response = requests.get(
        urljoin(
            settings.SAFERS_GATEWAY_API_URL,
            GET_TEAMS_URL_PATH,
        ),
        auth=ProxyAuthentication(user),
        params={"MaxResultCount": 1000}
    )
    response.raise_for_status()

    if user.is_remote:
        teams = [
            {
                "id": data["id"],
                "name": data["name"],
                "members": [
                    {
                        "id": member["id"],
                        "name": member["displayName"],
                    }
                    for member in data["members"]
                ]
            }
            for data in response.json()["data"]
        ]  # yapf: disable
    else:
        teams = []

    return Response(teams, status=status.HTTP_200_OK)
