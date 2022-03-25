from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from safers.users.models import UserProfile


def post_save_user_handler(sender, *args, **kwargs):
    """
    If a User has just been created,
    then the corresponding Profile must also be created,
    """
    created = kwargs.get("created", False)
    instance = kwargs.get("instance", None)
    if created and instance:
        UserProfile.objects.create(user=instance)


post_save.connect(
    post_save_user_handler,
    sender=get_user_model(),
    dispatch_uid="safers_post_save_user_handler",
)

# no signal handlers are needed for User post_delete because
# UserProfile and uses `on_delete=models.CASCADE`
