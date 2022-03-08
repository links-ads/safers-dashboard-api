from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fusionauth.fusionauth_client import FusionAuthClient

AUTH_CLIENT = FusionAuthClient(
    settings.FUSION_AUTH_API_KEY, settings.FUSION_AUTH_INTERNAL_BASE_URL
)
