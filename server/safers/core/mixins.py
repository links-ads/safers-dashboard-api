import hashlib

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


class HashableMixin(models.Model):
    class Meta:
        abstract = True

    _hash = models.UUIDField(blank=True, null=True)

    @property
    def hash(self):
        if self._hash:
            return self._hash.hex

    @property
    def hash_source(self):
        """
        Returns a hashable object to create the hash from.
        """
        msg = "The 'hash_source' property must be implemted for a Hashable model."
        raise NotImplementedError(msg)

    @classmethod
    def compute_hash(cls, hash_source):
        return hashlib.md5(hash_source).hexdigest()

    def has_hash_source_changed(self, new_hash_source):
        return self.hash != HashableMixin.compute_hash(new_hash_source)

    def save(self, *args, **kwargs):
        self._hash = HashableMixin.compute_hash(self.hash_source)
        return super().save(*args, **kwargs)
