from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from safers.core.models import SafersSettings


class AllowRegistrationPermission(BasePermission):
    ERROR_MSG = _("We are sorry, but registration is currently closed.")

    def has_permission(self, request, view):
        settings = SafersSettings.load()
        if not settings.allow_signup:
            # raising an error instead of returning False in order to get a custom message
            # as per https://github.com/encode/django-rest-framework/issues/3754#issuecomment-206953020
            raise PermissionDenied(self.ERROR_MSG)
        return True


class AllowLoginPermission(BasePermission):
    ERROR_MSG = _("We are sorry, but login is currently closed.")

    def has_permission(self, request, view):
        settings = SafersSettings.load()
        if not settings.allow_signin:
            # raising an error instead of returning False in order to get a custom message
            # as per https://github.com/encode/django-rest-framework/issues/3754#issuecomment-206953020
            raise PermissionDenied(self.ERROR_MSG)
        return True
