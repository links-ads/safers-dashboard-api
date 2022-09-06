from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

## REMOVED TIMESTAMP/BBOX FILTERING AS PER https://astrosat.atlassian.net/browse/SAFB-255
## from .serializers_base import DataViewSerializer
##
## class DataLayerViewSerializer(DataViewSerializer):
##     """
##     Note that this isn't a ModelSerializer; it's just being
##     used for query_param validation in the DataLayer Views
##     """
##
##     ProxyFieldMapping = {
##         # fields to pass onto proxy
##         "bbox": "Bbox",
##         "start": "Start",
##         "end": "End",
##         "include_map_requests": "IncludeMapRequests",
##     }
##
##     include_map_requests = serializers.BooleanField(
##         default=False,
##         required=False,
##         help_text=_(
##             "Whether or not to include on-demand MapRequests.  "
##             "This ought to be 'False' to distinguish this API from the 'api/data/map_requests' API."
##         ),
##     )


class DataLayerViewSerializer(serializers.Serializer):
    """
    Note that this isn't a ModelSerializer; it's just being
    used for query_param validation in the DataLayer Views
    """

    OrderType = models.TextChoices("OrderType", "date -date")
    ProxyFieldMapping = {
        # fields to pass onto proxy
        "include_map_requests": "IncludeMapRequests",
    }

    order = serializers.ChoiceField(choices=OrderType.choices, required=False)

    n_layers = serializers.IntegerField(
        default=1,
        required=False,
        help_text=_(
            "The number of recent layers to return for each data type. "
            "It is very unlikely you want to change this value."
        ),
    )

    include_map_requests = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_(
            "Whether or not to include on-demand MapRequests.  "
            "This ought to be 'False' to distinguish this API from the 'api/data/map_requests' API."
        ),
    )

    def validate_n_layers(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "n_layers must be greater thann 0."
            )
        return value
