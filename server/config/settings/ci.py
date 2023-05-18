"""
Custom settings for "ci" environment
"""
from .base import *

#########
# Setup #
#########

env = environ.Env()

DEBUG = True
SECRET_KEY = env("DJANGO_SECRET_KEY", default="shhh")
SECRET_KEY_FALLBACKS = env("DJANGO_SECRET_KEY_FALLBACKS", default=[])

########
# Apps #
########

INSTALLED_APPS += []
