from unittest import defaultTestLoader
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _


class CameraMediaType(models.TextChoices):
    IMAGE = "IMAGE", _("Image")
    VIDEO = "VIDEO", _("Video")


class CameraMediaManager(models.Manager):
    pass


class CameraMediaQuerySet(models.QuerySet):
    def images(self):
        return self.filter(type=CameraMediaType.IMAGE)

    def videos(self):
        return self.filter(type=CameraMediaType.VIDEO)

    def fire(self):
        return self.filter(is_fire=True)

    def smoke(self):
        return self.filter(is_smoke=True)

    def detected(self):
        return self.filter(Q(is_fire=True) | Q(is_smoke=True))

    def undetected(self):
        return self.filter(Q(is_fire=False) & Q(is_smoke=False))


class CameraMediaFireClass(models.Model):
    class Meta:
        verbose_name = "Fire Class"
        verbose_name_plural = "Fire Classes"

    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class CameraMedia(gis_models.Model):
    class Meta:
        verbose_name = "Camera Media"
        verbose_name_plural = "Camera Media"

    PRECISION = 12

    objects = CameraMediaManager.from_queryset(CameraMediaQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    camera = models.ForeignKey(
        "camera",
        related_name="media",
        blank=False,
        null=False,
        on_delete=models.CASCADE
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    type = models.CharField(
        max_length=64, choices=CameraMediaType.choices, blank=False, null=False
    )

    timestamp = models.DateTimeField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    url = models.URLField(
        max_length=512, blank=True, null=True
    )  # pre-signed AWS URLs can be quite long, hence the max_length kwarg

    is_smoke = models.BooleanField(default=False)
    is_fire = models.BooleanField(default=False)

    fire_classes = models.ManyToManyField(
        CameraMediaFireClass,
        blank=True,
        related_name="media",
        help_text=_(
            "A classification of the type of smoke detected from the camera."
            "Possible classes are: CL1 (fires involving wood/plants), CL2 (fires involving flammable materials/liquids), CL3 (fires involving gas)."
        )
    )

    direction = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        help_text=_(
            "The geographical direction in angles of the detected fire with respect to the camera location"
        )
    )
    distance = models.FloatField(
        blank=True,
        null=True,
        help_text=_(
            "The distance in meters of the detected fire with respect to the camera location"
        )
    )
    geometry = gis_models.GeometryField(blank=True, null=True)
