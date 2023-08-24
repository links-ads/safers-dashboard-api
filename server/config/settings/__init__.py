import environ
import glob

from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from config.types import EnvironmentTypes

###############
# setup stuff #
###############

BASE_DIR = Path(__file__).resolve(strict=True).parents[2]  # (server dir)

env = environ.Env(
    DJANGO_ENVIRONMENT=(EnvironmentTypes, EnvironmentTypes.DEVELOPMENT)
)

ENVIRONMENT = env("DJANGO_ENVIRONMENT")

############################################################
# load environment variables & appropriate settings module #
############################################################

if ENVIRONMENT == EnvironmentTypes.DEVELOPMENT:
    env_file = str(BASE_DIR / ".env")
    try:
        env.read_env(env_file)
    except Exception as e:
        raise ImproperlyConfigured(f"Unable to read '{env_file}': {e}.")

    from config.settings.development import *

elif ENVIRONMENT == EnvironmentTypes.DEPLOYMENT:
    env_file = str(BASE_DIR / ".env.deployment")
    try:
        env.read_env(env_file)
    except Exception as e:
        raise ImproperlyConfigured(f"Unable to read '{env_file}': {e}.")

    from config.settings.deployment import *

elif ENVIRONMENT == EnvironmentTypes.CI:
    pass  # variables for ci are hard-coded in actions

    from config.settings.ci import *

else:
    raise ImproperlyConfigured(f"Unknown ENVIRONMENT: '{ENVIRONMENT}'")

################
# heroku stuff #
################

import django_on_heroku

# django_on_heroku updates some features I've customised (such as S3 Storage and "postgis" database);
# I can prevent that by adding kwargs as per https://github.com/pkrefta/django-on-heroku#enabling-functionality
django_on_heroku.settings(locals(), geodjango=True, staticfiles=False)
