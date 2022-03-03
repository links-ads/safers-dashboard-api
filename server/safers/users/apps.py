from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.users'
    verbose_name = _("Safers Users")

    def ready(self):

        try:
            # register any checks...
            import safers.users.checks  
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.users.signals  
        except ImportError:
            pass

