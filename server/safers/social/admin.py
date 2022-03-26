from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from safers.social.models import Tweet


@admin.register(Tweet)
class TweetAdmin(gis_admin.GeoModelAdmin):
    fields = (
        "id",
        "tweet_id",
        # "geometry",
        # "bounding_box",
    )  # yapf: disable
    list_display = ("tweet_id", )
    readonly_fields = ("id", )
