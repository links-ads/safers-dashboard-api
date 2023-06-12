from django.db import models

from safers.core.clients import GATEWAY_CLIENT
from safers.core.managers import CachedTransientModelManager, TransientModelQuerySet

from safers.users.tests.mocks import MOCK_ORGANIZATIONS_DATA


class OrganizationQuerySet(TransientModelQuerySet):
    pass


class OrganizationManager(CachedTransientModelManager):

    queryset_class = OrganizationQuerySet

    cache_key = "organizations"

    def get_transient_queryset_data(self):
        organizations_data = GATEWAY_CLIENT.get_organizations(timeout=10)

        # organizations_data = MOCK_ORGANIZATIONS_DATA

        return organizations_data


class Organization(models.Model):
    class Meta:
        managed = False

    objects = OrganizationManager.from_queryset(OrganizationQuerySet)()

    id = models.IntegerField(primary_key=True)
    shortName = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    description = models.TextField(null=True)
    webSite = models.URLField(null=True)
    logoUrl = models.URLField(null=True)
    parentId = models.IntegerField(null=True)
    parentName = models.CharField(max_length=128, null=True)
    membersHaveTaxCode = models.BooleanField(null=True)
    hasChildren = models.BooleanField(null=True)

    def __str__(self) -> str:
        return str(self.name)

    @property
    def title(self) -> str:
        """
        Return a pretty name for the organization
        """
        return str(self).title().replace("_", " ")