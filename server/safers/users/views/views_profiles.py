import requests
from urllib.parse import urljoin

from django.conf import settings

from safers.users.authentication import ProxyAuthentication


def synchronize_profile(user_profile, user_profile_data):
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

    # merge remote profile data w/ local profile data...
    proxy_data = response.json()["profile"]
    proxy_data["user"].update(user_profile_data["user"])
    proxy_data["organizationId"] = user_profile_data["organizationId"]

    response = requests.put(
        urljoin(
            settings.SAFERS_GATEWAY_API_URL,
            SET_PROFILE_URL_PATH,
        ),
        auth=ProxyAuthentication(user),
        json=proxy_data
    )
    response.raise_for_status()

    return response.json()
