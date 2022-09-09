import uuid

from django.db import models


class OrganizationManager(models.Manager):
    pass


class OrganizationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class Organization(models.Model):

    objects = OrganizationManager.from_queryset(OrganizationQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    organization_id = models.SlugField(
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=128,
        blank=False,
        null=False,
        unique=True,
    )
    description = models.TextField(
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
