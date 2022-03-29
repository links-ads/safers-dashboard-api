import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import HashableMixin

# TODO: THIS IS ACTUALLY STORING A PROCESSED EVENT FROM THE SOCIAL MEDIA MODULE
# TODO: NOT AN INDIVIDUAL TWEET; IT INCLUDES AN ID THAT I CAN USE TO QUERY THE
# TODO: SOCIAL MEDIA API TO GET THE ACTUAL TWEETS THEMSELVES; THAT MUST BE DONE
# TODO: AT RUN-TIME B/C IT REQUIRES AUTHENCTICATION W/ THE API; THEREFORE I SHOULD
# TODO: RENAME ALL OF THESE CLASSES TO BE MORE PRECISE (ie: "SocialEvent" instead of "Tweet")


class TweetManager(models.Manager):
    pass


class TweetQuerySet(models.QuerySet):
    def filter_by_distance(self, target, distance=None):
        return self.filter()

    def filter_by_time(self, target, time=None):
        return self.filter()


class Tweet(HashableMixin, gis_models.Model):
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

    external_id = models.CharField(
        max_length=128,
        unique=True,
        blank=False,
        null=False,
    )

    type = models.CharField(max_length=128, blank=True, null=True)
    category = models.CharField(max_length=128, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    data = models.JSONField(default=dict)

    geometry = gis_models.GeometryField(blank=False, null=False)
    bounding_box = gis_models.PolygonField(blank=True, null=True)

    def __str__(self):
        return self.external_id

    @property
    def hash_source(self):
        return self.geometry.hexewkb

    def save(self, *args, **kwargs):
        if self.has_hash_source_changed(self.hash_source):
            if self.geometry.geom_type != "Point":
                self.bounding_box = self.geometry.envelope
        return super().save(*args, **kwargs)

    @classmethod
    def process_message(cls, message_body, message_properties={}):
        tweet, created = cls.objects.get_or_create(
            external_id=str(message_body["extId"])
        )
        tweet.type = message_body.get("type")
        tweet.category = message_body.get("category")
        tweet.start_date = message_body.get("startTS")
        tweet.end_date = message_body.get("endTS")
        tweet.geometry = message_body.get("locationData")
        tweet.data = message_body
        tweet.save()


#################
# SAMPLE TWEETS #
#################
"https://twitter.com/Brave_spirit81/status/1507386696635236362"  # (fire in Italy)
"https://twitter.com/NASA/status/1508587900849565703"  # (news from NASA)

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
  "includedData": [{
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
    }]
}  # yapf: disable