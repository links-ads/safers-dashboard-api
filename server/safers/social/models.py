import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _


class TweetManager(models.Manager):
    pass


class TweetQuerySet(models.QuerySet):
    def filter_by_distance(self, target, distance=None):
        return self.filter()

    def filter_by_time(self, target, time=None):
        return self.filter()


class Tweet(gis_models.Model):
    class Meta:
        verbose_name = "Tweet"
        verbose_name_plural = "Tweets"

    PRECISION = 12

    objects = TweetManager.from_queryset(TweetQuerySet)()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    tweet_id = models.IntegerField(
        blank=False,
        null=False,
        help_text=_("The numerical ID of the desired Tweet from Twitter."),
    )

    # geometry = gis_models.GeometryField(blank=False, null=False)
    # bounding_box = gis_models.PolygonField(blank=True, null=True)

    def __str__(self):
        return self.tweet_id