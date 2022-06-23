from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EventConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.events'
    verbose_name = _("Safers Events")

    def ready(self):

        try:
            # register any checks...
            import safers.events.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.events.signals
        except ImportError:
            pass
