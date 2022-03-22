from django.conf import settings
from django.core.checks import register, Error, Tags

# other apps required by tasks
APP_DEPENDENCIES = [
    "django_celery_beat",
    "django_celery_results",
]


@register(Tags.compatibility)
def check_dependencies(app_configs, **kwargs):
    """
    Makes sure that all django app dependencies are met.
    Called by `AppConfig.ready()`.
    """

    errors = []
    for i, dependency in enumerate(APP_DEPENDENCIES):
        if dependency not in settings.INSTALLED_APPS:
            errors.append(
                Error(
                    f"You are using safers.tasks which requires the {dependency} module.  Please install it and add it to INSTALLED_APPS.",
                    id=f"safers.tasks:E{i:03}",
                )
            )

    return errors
