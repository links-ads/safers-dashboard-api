import environ
import glob
import os
from importlib import import_module
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

import_module(environment_settings_module)

