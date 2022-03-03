from django.core.exceptions import ValidationError
from django.db import models


class SingletonMixin(models.Model):
    class Meta:
        abstract = True

    def clean(self):
        if not self.id and self.__class__.objects.count() > 0:
            raise ValidationError("Only one instance of a Singleton is allowed")

    def save(self, *args, **kwargs):
        if self.id or self.__class__.objects.count() == 0:
            # updating the existing instance
            # or creating the one-and-only instance
            super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
