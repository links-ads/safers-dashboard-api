from enum import Enum

from django.conf import settings
from django.db import models

from safers.auth.clients import AUTH_CLIENT
from safers.auth.utils import reshape_auth_errors

from safers.core.managers import CachedTransientModelManager, TransientModelQuerySet

from safers.users.tests.mocks import MOCK_ROLES_DATA


class RoleNames(str, Enum):
    CITIZEN = "citizen"


class RoleQuerySet(TransientModelQuerySet):

    pass


class RoleManager(CachedTransientModelManager):

    queryset_class = RoleQuerySet

    cache_key = "roles"

    def get_transient_queryset_data(self):
        auth_response = AUTH_CLIENT.retrieve_application(
            settings.FUSIONAUTH_APPLICATION_ID
        )
        if not auth_response.was_successful():
            errors = reshape_auth_errors(auth_response.error_response)
            raise Exception(errors)

        auth_application = auth_response.success_response.get("application")
        assert auth_application is not None
        roles_data = auth_application.get("roles", [])

        # roles_data = MOCK_ROLES_DATA

        return roles_data


class Role(models.Model):
    class Meta:
        managed = False

    objects = RoleManager.from_queryset(RoleQuerySet)()

    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
    isDefault = models.BooleanField(null=True)
    isSuperRole = models.BooleanField(null=True)

    def __str__(self) -> str:
        return str(self.name)

    @property
    def title(self) -> str:
        """
        Return a pretty name for the role
        """
        return str(self).title()

    @property
    def is_citizen(self) -> bool:
        return self.name == RoleNames.CITIZEN