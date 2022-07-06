from itertools import groupby

from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework_gis import serializers as gis_serializers

from safers.core.serializers import SwaggerCurrentUserDefault
from safers.data.models import MapRequest, DataType


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


class MapRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapRequest
        fields = (
            "id",
            "request_id",
            "title",
            "timestamp",
            "status",
            "user",
            "category",
            "parameters",
            "geometry",
            "data_types",
            "layers",
        )
        list_serializer_class = MapRequestListSerializer

    category = serializers.SerializerMethodField()
    layers = serializers.SerializerMethodField()
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

    def get_layers(self, obj):
        # TODO:
        return [{} for layer in obj.data_types.all()]

    def get_category(self, obj):
        groups = obj.data_types.values_list("group", flat=True)
        group = group = groups.distinct().first()
        return group.title()

    def validate_data_types(self, values):
        data_types_groups = set([v.group for v in values])
        if len(data_types_groups) != 1:
            raise serializers.ValidationError(
                "All DataTypes in a single MapRequest must belong to the same category."
            )

        return values
