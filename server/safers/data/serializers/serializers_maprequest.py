from itertools import groupby

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.core.serializers import SwaggerCurrentUserDefault
from safers.data.models import MapRequest, DataType

from .serializers_base import DataViewSerializer

############################
# view serializer          #
# (for proxy query_params) #
############################


class MapRequestViewSerializer(DataViewSerializer):
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
        default=True,
        required=False,
        help_text=_(
            "Whether or not to include on-demand MapRequests.  "
            "This ought to be 'True' to distinguish this API from the 'api/data/layers' API."
        ),
    )


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
            "url",
        )

    datatype_id = serializers.CharField(source="data_type.datatype_id")


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
