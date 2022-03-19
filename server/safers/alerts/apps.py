from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AlertsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.alerts'
    verbose_name = _("Safers Alerts")

    def ready(self):

        try:
            # register any checks...
            import safers.alerts.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.alerts.signals
        except ImportError:
            pass
