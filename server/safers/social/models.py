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


##########################
# SAMPLE MESSAGE PAYLOAD #
##########################
{
    "type": "Report",
    "extId": 14,
    "situationId": None,
    "category": "Wildfire",
    "severity": "MEDIUM",
    "startTS": "2021-11-11T10:47:46.496Z",
    "endTS": "2021-11-11T10:47:46.496Z",
    "status": "NONE",
    "description": "Wildfire in Italy",
    "locationData": {
        "coordinatePairs": [ -4.099245965096115, 53.37380543178034],
        "geometryType": "Point"
    },
    "includedData": [
        {
            "type": "SocialMediaContent",
            "fullLocationData": {
                "geometryType": "MultiPolygon",
                "coordinatePairs": [
                    [
                        [
                            [-0.3209221, 61.061],
                            [2.09191170, 61.061],
                            [2.09191170, 49.674],
                            [-14.015517, 49.674],
                            [-14.015517, 54.433],
                            [-14.015517, 61.061],
                            [-0.3209221, 61.061]
                        ]
                    ]
                ]
            },
            "created": "2021-11-11T10:47:46.496Z",
            "source": {
                "id": "socialmediasource",
                "providerId" : "SocialMediaSource",
                "name": "Twitter",
                "dataSourceType": "SocialMediaSource"
            },
            "language": "it",
            "hazard_id": "wildfire"
        }
    ]
}  # yapf: disable