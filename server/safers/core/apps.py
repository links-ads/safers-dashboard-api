from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'safers.core'

    try:
        # register any checks...
        import safers.core.checks  
    except ImportError:
        pass

    try:
        # register any signals...
        import safers.core.signals  
    except ImportError:
        pass

