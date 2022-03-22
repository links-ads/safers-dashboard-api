from dataclasses import dataclass

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from knox.models import AuthToken as KnoxToken
from knox.settings import knox_settings


@dataclass
class KnoxData:
    instance: KnoxToken
    key: str


def create_knox_token(token_model, user, serializer):
    """
    used by dj-rest-auth to add LoginSerializer.token, etc.
    """
    token_limit_per_user = knox_settings.TOKEN_LIMIT_PER_USER
    if token_limit_per_user is not None:
        now = timezone.now()
        tokens = user.auth_token_set.filter(expiry__gt=now)
        assert tokens.count() <= token_limit_per_user, "Maximum amount of tokens allowed per user exceeded."

    token_instance, token_key = KnoxToken.objects.create(user=user)
    return KnoxData(token_instance, token_key)
