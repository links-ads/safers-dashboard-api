import uuid

from django.db import models


class RoleManager(models.Manager):
    def safe_get(self, *args, **kwargs):
        """
        models that aren't stored locally (like the chatbot models)
        sometimes try to reference Role that might not exist
        this allows me to cope w/ those cases
        """
        try:
            return Role.objects.get(*args, **kwargs)
        except Role.DoesNotExist:
            return None


class RoleQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class Role(models.Model):

    objects = RoleManager.from_queryset(RoleQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    role_id = models.SlugField(
        blank=True,
        null=True,
    )
    name = models.CharField(
        max_length=128,
        blank=False,
        null=False,
        unique=True,
    )
    label = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )
    description = models.TextField(
        blank=True,
        null=True,
    )
    is_default = models.BooleanField(default=False)
    is_super = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
