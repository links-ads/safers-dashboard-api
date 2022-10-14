import requests
from enum import Enum
from urllib.parse import urljoin

from django.conf import settings

from safers.users.authentication import ProxyAuthentication
from safers.users.models import Organization, Role
from safers.users.serializers import UserSerializer


class SynchronizeProfileDirection(Enum):
    LOCAL_TO_REMOTE = 1
    REMOTE_TO_LOCAL = 2


def synchronize_profile(user_profile, direction):
    # TODO: Refactor UserProfile to match FusionAuth
    # TODO: And make this a proper DRF view

    user = user_profile.user

    GET_PROFILE_URL_PATH = "/api/services/app/Profile/GetProfile"
    SET_PROFILE_URL_PATH = "/api/services/app/Profile/UpdateProfile"

    response = requests.get(
        urljoin(
            settings.SAFERS_GATEWAY_API_URL,
            GET_PROFILE_URL_PATH,
        ),
        auth=ProxyAuthentication(user)
    )
    response.raise_for_status()
    profile_data = response.json()["profile"]

    if direction == SynchronizeProfileDirection.REMOTE_TO_LOCAL:
        roles = Role.objects.filter(
            name__in=(profile_data.get("user") or {}).get("roles", [])
        )
        organizations = Organization.objects.active().filter(
            organization_id=(profile_data.get("organization") or {}).get("id")
        )
        user_serializer = UserSerializer()
        user_serializer.update(
            user,
            {
                "profile": {
                    "first_name": profile_data["user"].get("firstName"),
                    "last_name": profile_data["user"].get("lastName"),
                },
                "role": roles.first(),
                "organization": organizations.first(),
            }
        )

    elif direction == SynchronizeProfileDirection.LOCAL_TO_REMOTE:
        profile_data["user"].update({
            "email": user.email,
            "firstName": user_profile.first_name,
            "lastName": user_profile.last_name,
            "roles": [user.role.name] if user.role else [],
        })
        profile_data["organizationId"] = int(
            user.organization.organization_id
        ) if user.is_professional else None
        response = requests.put(
            urljoin(
                settings.SAFERS_GATEWAY_API_URL,
                SET_PROFILE_URL_PATH,
            ),
            auth=ProxyAuthentication(user),
            json=profile_data,
        )
        response.raise_for_status()

    else:
        raise ValueError("invalid SynchronizeProfileDirection")
