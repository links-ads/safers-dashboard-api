from django.conf import settings

from fusionauth.fusionauth_client import FusionAuthClient

AUTH_CLIENT = FusionAuthClient(
    settings.FUSIONAUTH_API_KEY, settings.FUSIONAUTH_INTERNAL_URL
)
