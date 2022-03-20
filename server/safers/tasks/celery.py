import os
from celery import Celery, shared_task

import django
from django.apps import apps
from django.conf import settings

assert "DJANGO_SETTINGS_MODULE" in os.environ

if not settings.configured:
    # let's me use "apps" below, when called from run-celery.sh
    django.setup()

app = Celery(settings.PROJECT_SLUG)
app.config_from_object("django.conf:settings", namespace="CELERY")

installed_apps = [app_config.name for app_config in apps.get_app_configs()]
app.autodiscover_tasks(lambda: installed_apps, related_name="tasks", force=True)

# NOTE: DO NOT FORGET THAT INVALID TASKS WILL NOT RAISE AN ERROR.
# NOTE: THEY WILL JUST NOT BE DISCOVERED; SO IF SOMETHING DOESN'T
# NOTE: SHOW UP IN THE BEAT DB SCHEDULER, THAT'S LIKELY TO BE WHY.
# NOTE: TO CHECK THIS JUST RUN `from <app> import tasks` FOR THE
# NOTE: PROBLEMETIC TASK AND SEE IF ANY ERRORS ARE REPORTED


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
