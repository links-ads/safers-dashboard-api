import environ
import glob
import os

from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

###############
# setup stuff #
###############

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

ENVIRONMENT = os.environ.get("SYS_ENV", "development")
environment_settings_module = f"config.settings.{ENVIRONMENT}"

##############################
# load environment variables #
##############################

env = environ.Env()

if ENVIRONMENT == "development":
    # environment variables for development are stored in files
    for env_file in glob.glob(str(BASE_DIR / ".env*")):
        try:
            env.read_env(env_file)
        except Exception as e:
            msg = f"Unable to read '{env_file}': {e}."
            raise ImproperlyConfigured(msg)
else:
    # otherwise, they are dynamically-created during deployment
    pass

###################
# import settings #
###################

from .base import *

exec(f"from {environment_settings_module} import *") in globals()

import django_on_heroku
django_on_heroku.settings(locals())
