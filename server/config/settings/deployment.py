from .base import *
from .base import env

DEBUG = True

SECRET_KEY = env("DJANGO_SECRET_KEY")

CORS_ORIGIN_ALLOW_ALL = True

#########
# email #
#########

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

DEFAULT_FROM_EMAIL = "noreply@safers.com"
SERVER_EMAIL = "noreply@safers.com"

ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY", default=""),
    # don't need these yet...
    # "MAILGUN_DOMAIN":
    #     env("MAILGUN_DOMAIN", default=""),
    # "MAILGUN_PUBLIC_KEY":
    #     env("MAILGUN_PUBLIC_KEY", default=""),
    # "MAILGUN_WEBHOOK_SIGNING_KEY":
    #     env("MAILGUN_WEBHOOK_SIGNING_KEY", default=""),
    # "MAILGUN_SENDER_DOMAIN":
    #     env("MAILGUN_SENDER_DOMAIN", default=""),
}
