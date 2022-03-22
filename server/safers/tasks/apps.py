from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.tasks'
    verbose_name = _("Tasks")

    def ready(self):

        try:
            # register any checks...
            import safers.tasks.checks
        except ImportError:
            pass

        try:
            # register any signals...
            import safers.tasks.signals
        except ImportError:
            pass

        # load celery !
        import safers.tasks.celery
