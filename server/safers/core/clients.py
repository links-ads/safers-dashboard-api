import requests
from urllib.parse import urljoin, urlencode

from django.conf import settings

REQUEST_TIMEOUT = 4

requests_session = requests.Session()

# TODO: CAN PreparedRequests HELP SPEED THINGS UP ?
# TODO: (as per https://requests.readthedocs.io/en/latest/user/advanced/#prepared-requests)


class GatewayClient(object):

    PROFILE_PATH = "api/services/app/Profile"

    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    def get_organizations(
        self, params=None, auth=None, timeout=REQUEST_TIMEOUT
    ) -> dict:
        url = urljoin(
            settings.SAFERS_GATEWAY_URL,
            f"{self.PROFILE_PATH}/GetOrganizations"
        )

        default_params = {"MaxResultCount": 1000}
        if params:
            default_params.update(params)

        response = requests_session.request(
            method="GET",
            headers=self.headers,
            url=url,
            params=default_params,
            auth=auth,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()


GATEWAY_CLIENT = GatewayClient()