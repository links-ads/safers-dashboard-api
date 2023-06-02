from django.conf import settings
from django.core.exceptions import BadRequest
from django.utils.functional import cached_property

from fusionauth.fusionauth_client import FusionAuthClient

from safers.auth.utils import reshape_auth_errors


class SafersFusionAuthClient(FusionAuthClient):
    """
    A wrapper around the existing FusionAuthClient to add some custom
    safers-specific functionality
    """
    @cached_property
    def settings(self):
        """
        Returns information about how FusionAuth is configured
        """
        auth_response = self.retrieve_application(
            settings.FUSIONAUTH_APPLICATION_ID
        )
        if not auth_response.was_successful():
            errors = reshape_auth_errors(auth_response.error_response)
            raise BadRequest(errors)

        auth_application = auth_response.success_response.get("application")
        settings_data = auth_application.get("jwtConfiguration", {})

        return {
            "refresh_token_expiration_policy": settings_data["refreshTokenExpirationPolicy"],
            "refresh_token_usage_policy": settings_data["refreshTokenUsagePolicy"],
            "refresh_token_time_to_live": settings_data["refreshTokenTimeToLiveInMinutes"] * 60,
            "access_token_time_to_live": settings_data["timeToLiveInSeconds"],
        }  # yapf: disable


AUTH_CLIENT = SafersFusionAuthClient(
    settings.FUSIONAUTH_API_KEY, settings.FUSIONAUTH_INTERNAL_URL
)
