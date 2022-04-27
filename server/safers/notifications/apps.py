from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.notifications'
    verbose_name = _("Safers Notifications")

    def ready(self):

        try:
            # register any checks...
            import safers.notifications.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.notifications.signals
        except ImportError:
            pass
