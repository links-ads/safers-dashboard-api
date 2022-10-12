import uuid

from django.db import models


class OrganizationManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)

    def safe_get(self, *args, **kwargs):
        """
        models that aren't stored locally (like the chatbot models)
        sometimes try to reference Organizations that might not exist
        this allows me to cope w/ those cases
        """
        try:
            return Organization.objects.get(*args, **kwargs)
        except Organization.DoesNotExist:
            return None


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

    def natural_key(self):
        return (self.name, )
