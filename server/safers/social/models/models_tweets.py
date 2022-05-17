import uuid

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext_lazy as _


class TweetLanguageType(models.TextChoices):
    EN = "en", _("English")
    IT = "it", _("Italian")
    ES = "es", _("Spanish")
    HR = "hr", _("Croatian")
    TR = "tr", _("Turkish")
    FI = "fi", _("Finnish")
    el = "el", _("Greek")
    FR = "fr", _("French")
    NL = "nl", _("Dutch")


class TweetHazardType(models.TextChoices):
    ACCIDENT = "accident", _("Accident"),
    AVALANCHE = "avalanche", _("avalanche")
    COLLAPSE = "collapse", _("Collapse")
    EARTHQUAKE = "earthquake", _("Earthquake")
    FLOOD = "flood", _("Flood")
    LANDSLIDE = "landslide", _("Landslide")
    PANDEMIC = "pandemic", _("Pandemic")
    STORM = "storm", _("Storm")
    SUBSIDENCE = "subsidence", _("Subsidence")
    TEMPERATURE = "temp_anomaly", _("Temperature anomaly")
    TERRORISM = "terrorism", _("Terrorism")
    WILDFIRE = "wildfire", _("Wildfire")


class TweetInfoType(models.TextChoices):
    CAUTION = "caution_advice", _("Caution and advice")
    DONATION = "donation_volunteer", _("Donations, volunteering or rescue efforts")
    INFRASTRUCTURE = "infrastructure_utilities", _("Infrastructure and utilities")
    INJURED = "people_injured_dead", _("Injured or dead people")
    MISSING = "people_missing_found", _("Missing or found people")
    NA = "not_relevant", _("Irrelevant information")
    OTHER = "other_info", _("Other useful information")
    PEOPLE_AFFECTED = "people_affected", _("Affected people")
    SYMPATHY = "sympathy", _("Sympathy and Support")


class Tweet(gis_models.Model):
    # pretty minimal model b/c I don't actually store these in the db
    class Meta:
        verbose_name = "Tweet"
        verbose_name_plural = "Tweets"

    PRECISION = 12

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    tweet_id = models.CharField(
        max_length=128, unique=True, blank=False, null=False
    )
    timestamp = models.DateTimeField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    geometry = gis_models.GeometryField(blank=False, null=False)


#################
# SAMPLE TWEETS #
#################
"https://twitter.com/Brave_spirit81/status/1507386696635236362"  # (fire in Italy)
"https://twitter.com/NASA/status/1508587900849565703"  # (news from NASA)
