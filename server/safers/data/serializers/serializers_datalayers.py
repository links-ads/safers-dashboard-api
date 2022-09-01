from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from .serializers_base import DataViewSerializer


class DataLayerViewSerializer(DataViewSerializer):
    """
    Note that this isn't a ModelSerializer; it's just being
    used for query_param validation in the DataLayer Views
    """

    ProxyFieldMapping = {
        # fields to pass onto proxy
        "bbox": "Bbox",
        "start": "Start",
        "end": "End",
        "include_map_requests": "IncludeMapRequests",
    }

    include_map_requests = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_(
            "Whether or not to include on-demand MapRequests.  "
            "This ought to be 'False' to distinguish this API from the 'api/data/map_requests' API."
        ),
    )
