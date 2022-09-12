from itertools import groupby

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.core.serializers import SwaggerCurrentUserDefault
from safers.data.models import MapRequest, DataType

## REMOVED TIMESTAMP/BBOX FILTERING AS PER https://astrosat.atlassian.net/browse/SAFB-255
##
## from .serializers_base import DataViewSerializer
##
## class MapRequestViewSerializer(DataViewSerializer):
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
##         default=True,
##         required=False,
##         help_text=_(
##             "Whether or not to include on-demand MapRequests.  "
##             "This ought to be 'False' to distinguish this API from the 'api/data/map_requests' API."
##         ),
##     )


class MapRequestViewSerializer(serializers.Serializer):
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
        default=True,
        required=False,
        help_text=_(
            "Whether or not to include on-demand MapRequests.  "
            "This ought to be 'True' to distinguish this API from the 'api/data/layers' API."
        ),
    )

    def validate_n_layers(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "n_layers must be greater than 0."
            )
        return value


##########################
# model serializer       #
# (for normal DRF stuff) #
##########################


class MapRequestListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        """
        reshape data to group by category; (using itertools instead 
        of built-in django methods b/c "category" is not a field)
        """
        representation = super().to_representation(data)
        grouped_representation = groupby(
            representation, key=lambda x: x["category"]
        )
        return [
            {
                "key": f"{i}",
                "category": key,
                "requests": [
                    dict(
                        key=f"{i}.{j}",
                        layers=[
                            dict(
                                key=f"{i}.{j}.{k}",
                                **layer,
                            )
                            for k, layer in enumerate(group_member.pop("layers"), start=1)
                        ],
                        **group_member,
                    )
                    for j, group_member in enumerate(group, start=1)
                ],
            }
            for i, (key, group) in enumerate(grouped_representation, start=1)
        ] # yapf: disable

class MapRequestDataTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapRequest.data_types.through
        fields = (
            "datatype_id",
            "status",
            "datatype_name",
            "proxy_details",
        )

    datatype_id = serializers.CharField(source="data_type.datatype_id")
    datatype_name = serializers.CharField(source="data_type.description")
    proxy_details = serializers.SerializerMethodField()

    def get_proxy_details(self, obj):
        request_id = obj.map_request.request_id
        datatype_id = obj.data_type.datatype_id
        proxy_details = self.context.get("proxy_details", {})
        return proxy_details.get(request_id, {}).get(datatype_id, {})

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.update(representation.pop("proxy_details"))
        return representation


class MapRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapRequest
        fields = (
            "id",
            "request_id",
            "title",
            "timestamp",
            "user",
            "category",
            "parameters",
            "geometry",
            "geometry_wkt",
            "layers",  # (read)
            "data_types",  # (write)
        )
        list_serializer_class = MapRequestListSerializer

    request_id = serializers.CharField(read_only=True)
    category = serializers.SerializerMethodField()
    layers = MapRequestDataTypeSerializer(
        many=True, read_only=True, source="map_request_data_types"
    )
    geometry = gis_serializers.GeometryField(precision=MapRequest.PRECISION)
    timestamp = serializers.DateTimeField(source="created", read_only=True)

    data_types = serializers.SlugRelatedField(
        slug_field="datatype_id",
        write_only=True,
        many=True,
        queryset=DataType.objects.on_demand(),
    )

    user = serializers.PrimaryKeyRelatedField(
        default=SwaggerCurrentUserDefault(),
        queryset=get_user_model().objects.all(),
    )

    def get_category(self, obj):
        groups = obj.data_types.values_list("group", flat=True)
        group = group = groups.distinct().first()
        if group:
            return group.title()

    def validate_data_types(self, values):
        data_types_groups = set([v.group for v in values])

        if not values:
            raise serializers.ValidationError(
                "A MapRequest must have at least one DataType"
            )

        if len(data_types_groups) != 1:
            raise serializers.ValidationError(
                "All DataTypes in a single MapRequest must belong to the same category."
            )

        return values
