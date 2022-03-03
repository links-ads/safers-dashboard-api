"""
Django settings for safers-gateway project.
"""

import environ
from pathlib import Path

from django.utils.html import escape
from django.utils.text import slugify

env = environ.Env()

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
APP_DIR = BASE_DIR / "safers"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

PROJECT_NAME = "Safers Gateway"
PROJECT_SLUG = slugify(PROJECT_NAME)

# DEBUG & SECRET_KEY are overridden in environment-specific settings
DEBUG = True
SECRET_KEY = 'shhh...'

SITE_ID = 1

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ALLOWED_HOSTS = []


# Application definition

DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.admin',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_gis',
    'django_celery_beat',
    'django_celery_results',
    'drf_yasg',
]   

LOCAL_APPS = [
    'safers.core',
    'safers.users',
    # 'safers.tasks',
    # 'safers.alerts',
    # 'safers.events',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ATOMIC_REQUESTS": True,
#         "ENGINE": "django.contrib.gis.db.backends.postgis",
#         "NAME": env("DJANGO_DB_NAME", default=""),
#         "USER": env("DJANGO_DB_USER", default=""),
#         "PASSWORD": env("DJANGO_DB_PASSWORD", default=""),
#         "HOST": env("DJANGO_DB_HOST", default="db"),
#         "PORT": env("DJANGO_DB_PORT", default="5432"),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    # make Argon2 the default password hasher (as per https://docs.djangoproject.com/en/4.0/topics/auth/passwords/#using-argon2-with-django)
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    # 'django.contrib.auth.hashers.ScryptPasswordHasher',
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


################
# Static Files #
################

STATIC_URL = '/static/'
STATIC_ROOT = str(APP_DIR / "static")


#########
# Admin #
#########

ADMIN_URL = "admin/"

ADMIN_SITE_HEADER = f"{PROJECT_NAME} administration console"
ADMIN_SITE_TITLE = f"{PROJECT_NAME} administration console"
ADMIN_INDEX_TITLE = f"Welcome to the {PROJECT_NAME} administration console"

# API


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ]
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": escape("Enter 'Token <token>'"),
        },
        "Basic": {
            "type": "basic"
        },
    },
    "DOC_EXPANSION": "none",
    "OPERATIONS_SORTER": None,
    "TAGS_SORTER": "alpha",
    "DEFAULT_MODEL_RENDERING": "example",
}

#################
# Authentiation #
#################

AUTH_USER_MODEL = "users.User"

FUSION_AUTH_APP_ID = env("FUSION_AUTH_APP_ID", default="")
FUSION_AUTH_CLIENT_SECRET = env("FUSION_AUTH_CLIENT_SECRET", default="")
FUSION_AUTH_API_KEY = env("FUSION_AUTH_API_KEY", default="")
FUSION_AUTH_BASE_URL = env("FUSION_AUTH_BASE_URL", default="") 

# GOOGLE_OAUTH_CLIENT_ID = "230917725684-gc2nk79fpo1op20sv2i5q9h8baf642l6.apps.googleusercontent.com"
# GOOGLE_OAUTH_CLIENT_SECRET = "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"