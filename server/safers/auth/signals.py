import logging

from django.contrib.auth import get_user_model
from django.dispatch import Signal, receiver

logger = logging.getLogger(__name__)

user_registered_signal = Signal()

UserModel = get_user_model()


@receiver(
    user_registered_signal,
    dispatch_uid="safers_user_registered_signal_handler",
)
def user_registered_signal_handler(sender, **kwargs):
    instance = kwargs.get("instance")
    request = kwargs.get("request")
    logger.info(f"User '{instance}' registered.")