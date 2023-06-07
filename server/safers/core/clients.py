import requests
from urllib.parse import urljoin, urlencode

from django.conf import settings

REQUEST_TIMEOUT = 4

requests_session = requests.Session()

# TODO: CAN PreparedRequests HELP SPEED THINGS UP ?
# TODO: (as per https://requests.readthedocs.io/en/latest/user/advanced/#prepared-requests)


class GatewayClient(object):

    ACTIVITY_PATH = "api/services/app/Activity"
    LAYERS_PATH = "api/services/app/Layers"
    PROFILE_PATH = "api/services/app/Profile"

    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
    }

    def get_profile(self, params=None, auth=None, timeout=REQUEST_TIMEOUT):
        url = urljoin(
            settings.SAFERS_GATEWAY_URL, f"{self.PROFILE_PATH}/GetProfile"
        )
        response = requests_session.request(
            method="GET",
            headers=self.headers,
            url=url,
            params=params,
            auth=auth,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    def update_profile(self, data=None, auth=None, timeout=REQUEST_TIMEOUT):
        url = urljoin(
            settings.SAFERS_GATEWAY_URL, f"{self.PROFILE_PATH}/UpdateProfile"
        )
        response = requests_session.request(
            method="PUT",
            headers=self.headers,
            url=url,
            json=data,
            auth=auth,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

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

        # follow all parent organizations...
        organizations_data = response.json()["data"]
        for organization in organizations_data:
            if organization["hasChildren"]:
                organizations_data += self.get_organizations(
                    params=dict(
                        parentId=organization["id"],
                        **default_params,
                    ),
                    auth=auth,
                    timeout=timeout,
                )

        return organizations_data

    def get_layers(
        self, params=None, auth=None, timeout=REQUEST_TIMEOUT
    ) -> dict:
        url = urljoin(
            settings.SAFERS_GATEWAY_URL, f"{self.LAYERS_PATH}/GetLayers"
        )

        default_params = {}
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