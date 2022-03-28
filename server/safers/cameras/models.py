import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin


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

    def filter_by_distance(self, target, distance=None):
        return self.filter()

    def filter_by_time(self, target, time=None):
        return self.filter()


class Camera(gis_models.Model):
    class Meta:
        verbose_name = "Camera"
        verbose_name_plural = "Cameras"

    PRECISION = 12

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=128, blank=True, null=True, unique=True)
    description = models.TextField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)
    geometry = gis_models.PointField(blank=False, null=False)

    def __str__(self) -> str:
        return self.name


class CameraMediaTag(models.Model):
    class Meta:
        verbose_name = "Camera Media Tag"
        verbose_name_plural = "Camera Media Tags"

    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class CameraMedia(HashableMixin, gis_models.Model):
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

    type = models.CharField(
        max_length=64, choices=CameraMediaType.choices, blank=False, null=False
    )
    tags = models.ManyToManyField(CameraMediaTag, related_name="media")
    camera = models.ForeignKey(
        Camera,
        related_name="media",
        blank=False,
        null=False,
        on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    smoke_column_class = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text=_(
            "A classification of the type of smoke detected from the camera."
            "Possible classes are: CL1 (fires involving wood/plants), CL2 (fires involving flammable materials/liquids), CL3 (fires involving gas)."
        )
    )
    geographical_direction = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        help_text=_(
            "The geographical direction in angles of the detected fire with respect to the camera location"
        )
    )
    geometry = gis_models.GeometryField(blank=False, null=False)
    bounding_box = gis_models.PolygonField(blank=True, null=True)

    @property
    def hash_source(self):
        # TODO: INCORPORATE CAMERA.ID INTO HASH_SOURCE
        return self.geometry.hexewkb

    def save(self, *args, **kwargs):
        if self.has_hash_source_changed(self.hash_source):
            if self.geometry.geom_type != "Point":
                self.bounding_box = self.geometry.envelope
        return super().save(*args, **kwargs)
