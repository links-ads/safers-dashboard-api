import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _


class CameraManager(models.Manager):
    pass


class CameraQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class Camera(gis_models.Model):
    class Meta:
        verbose_name = "Camera"
        verbose_name_plural = "Cameras"

    PRECISION = 12
    MIN_BOUNDING_BOX_SIZE = 0.00001  # TODO: NOT SURE WHAT THIS SHOULD BE

    objects = CameraManager.from_queryset(CameraQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    camera_id = models.CharField(
        max_length=128,
        blank=False,
        null=False,
        unique=True,
    )

    is_active = models.BooleanField(default=True)

    name = models.CharField(max_length=128, blank=True, null=True)
    model = models.CharField(max_length=128, blank=True, null=True)
    owner = models.CharField(max_length=128, blank=True, null=True)
    nation = models.CharField(max_length=128, blank=True, null=True)
    altitude = models.FloatField(
        blank=True,
        null=True,
        help_text=_("The altitude of the camera in meters.")
    )
    direction = models.FloatField(
        blank=False,
        null=False,
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        help_text=_(
            "The angle of camera orientation, where 0 means North, 90 East, 180 South and 270 West"
        )
    )
    geometry = gis_models.PointField(blank=False, null=False)

    last_update = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.camera_id

    def recalculate_last_update(self, ignore=[]):
        """
        called in response to an associated CameraMedia object being saved/deleted
        """
        most_recent_camera_media_timestamp = self.media.exclude(
            pk__in=[camera_media.pk for camera_media in ignore]
        ).order_by("timestamp").values_list("timestamp", flat=True).last()
        self.last_update = most_recent_camera_media_timestamp
        self.save()
