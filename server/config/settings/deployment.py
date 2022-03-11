from .base import *
from .base import env

DEBUG = True

SECRET_KEY = env("DJANGO_SECRET_KEY")

CORS_ORIGIN_ALLOW_ALL = True

#########
# email #
#########

# TODO: I ACTUALLY WANT TO USE A "PROPER ESP VIA ANYMAIL
# TODO: (LIKE SENDMAIL VIA HEROKU), BUT IT TAKES TIME TO
# TODO: SET UP PROPERLY.  SO FOR NOW I'M USING GMAIL :(
# EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
# DEFAULT_FROM_EMAIL = "noreply@safers.com"
# SERVER_EMAIL = "noreply@safers.com"
# ANYMAIL = {
#     "MAILGUN_API_KEY":
#         env("MAILGUN_API_KEY", default=""),
#     "MAILGUN_DOMAIN":
#         env("MAILGUN_DOMAIN", default=""),
#     "MAILGUN_PUBLIC_KEY":
#         env("MAILGUN_PUBLIC_KEY", default=""),
#     "MAILGUN_SMTP_LOGIN":
#         env("MAILGUN_SMTP_LOGIN", default=""),
#     "MAILGUN_SMTP_PASSWORD":
#         env("MAILGUN_SMTP_PASSWORD", default=""),
#     "MAILGUN_SMTP_PORT":
#         env("MAILGUN_SMTP_PORT", default=""),
#     "MAILGUN_SMTP_SERVER":
#         env("MAILGUN_SMTP_SERVER", default=""),
#     "MAILGUN_WEBHOOK_SIGNING_KEY":
#         env("MAILGUN_WEBHOOK_SIGNING_KEY", default=""),
#     "MAILGUN_SENDER_DOMAIN":
#         env("MAILGUN_SENDER_DOMAIN", default=""),
# }

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env("EMAIL_HOST_PORT", default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

DEFAULT_FROM_EMAIL = env("EMAIL_HOST_USER", default=EMAIL_HOST_USER)
