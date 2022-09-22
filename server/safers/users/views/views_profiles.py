import requests
from urllib.parse import urljoin

from django.conf import settings

from safers.users.authentication import ProxyAuthentication


def synchronize_profile(user_profile, user_profile_data):
    # TODO: Refactor UserProfile to match FusionAuth
    # TODO: And make this a proper DRF view
    user = user_profile.user
    PROFILE_URL_PATH = "/api/services/app/Profile/UpdateProfile"
    response = requests.put(
        urljoin(
            settings.SAFERS_GATEWAY_API_URL,
            PROFILE_URL_PATH,
        ),
        auth=ProxyAuthentication(user),
        json=user_profile_data
    )
    response.raise_for_status()
    return response.json()
