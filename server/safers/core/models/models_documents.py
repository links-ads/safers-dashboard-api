from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify

###########
# helpers #
###########


def document_file_path(instance, filename):
    return f"documents/{filename}"


##############
# validators #
##############


@deconstructible
class FileSizeValidator(object):
    # using a class instead of a fn to allow it to take arguments

    size_units = ["B", "KB", "MB"]

    def __init__(self, max_size, max_size_units="MB"):

        assert max_size_units in self.size_units, f"max_size_units must be one of {', '.join(self.size_units)}"

        self.max_size = max_size
        self.max_size_units = max_size_units

    def __call__(self, value):
        file_size = value.size
        if self.max_size_units == "KB":
            file_size /= 1000
        elif self.max_size_units == "MB":
            file_size /= 1000000

        if file_size > self.max_size:
            raise ValidationError(
                f"The maximum file size is {self.max_size} {self.max_size_units}."
            )


############
# managers #
############


class DocumentManager(models.Manager):
    pass


class DocumentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


##########
# models #
##########


class Document(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "version"], name="unique_name_version"
            ),
        ]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    objects = DocumentManager.from_queryset(DocumentQuerySet)()

    name = models.CharField(max_length=128, blank=False, null=False)
    version = models.CharField(max_length=32, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(
        max_length=128 + 32, editable=False, blank=False, null=False
    )

    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    file = models.FileField(
        upload_to=document_file_path,
        validators=[FileExtensionValidator(["pdf"]), FileSizeValidator(16)],
    )

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="documents",
        through="DocumentAgreement",
    )

    def __str__(self):
        return " - ".join(filter(None, [self.name, self.version]))

    @property
    def file_exists(self):
        return self.file.storage.exists(self.file.path)

    @property
    def has_agreements(self):
        return self.n_agreements > 0

    @property
    def n_agreements(self):
        return self.agreements.count()

    def save(self, *args, **kwargs):
        self.slug = slugify(str(self))
        return super().save(*args, **kwargs)


class DocumentAgreement(models.Model):
    """
    A "through" model for the relationship between Documents & Users
    """
    class Meta:
        ordering = ["-timestamp"]

    # b/c the extra fields on this through model have default values
    # (auto_add_now), I can just do `user.documents.add(document)` instead of
    # bothering w/ `DocumentAgreement.objects.get_or_create(...)`

    document = models.ForeignKey(
        Document, on_delete=models.PROTECT, related_name="agreements"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agreements",
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.document}: {self.user}"
