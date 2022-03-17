from django.contrib.auth import get_user_model

from allauth.account.signals import user_signed_up

from safers.users.models import UserProfile


def user_signed_up_handler(sender, *args, **kwargs):
    """
    If a local user has just signed-up (via dj-rest-auth),
    then the corresponding profile must also be created.
    """
    user = kwargs.get("user", None)
    if user:
        UserProfile.objects.create(user=user)


user_signed_up.connect(
    user_signed_up_handler,
    sender=get_user_model(),
    dispatch_uid="safers_user_signed_up_handler",
)

# no signal handlers are needed for User post_delete because
# UserProfile and Oauth2User both use `on_delete=models.CASCADE`