from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from knox.models import AuthToken as KnoxToken
from knox.settings import knox_settings

from fusionauth.fusionauth_client import FusionAuthClient

AUTH_CLIENT = FusionAuthClient(
    settings.FUSION_AUTH_API_KEY, settings.FUSION_AUTH_INTERNAL_BASE_URL
)


def create_knox_token(token_model, user, serializer):
    token_limit_per_user = knox_settings.TOKEN_LIMIT_PER_USER
    if token_limit_per_user is not None:
        now = timezone.now()
        tokens = user.auth_token_set.filter(expiry__gt=now)
        assert tokens.count() <= token_limit_per_user, "Maximum amount of tokens allowed per user exceeded."

    token_instance, token_key = KnoxToken.objects.create(user=user)
    return token_instance
