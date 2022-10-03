# Generated by Django 3.2.15 on 2022-10-03 11:05

import json
from django.db import migrations


def compute_geometry_features(apps, schema_editor):

    MapRequestModel = apps.get_model("data", "MapRequest")

    for map_request in MapRequestModel.objects.all():
        if map_request.geometry:
            map_reqeust_geometry_geojson = json.loads(
                map_request.geometry.geojson
            )
            if map_reqeust_geometry_geojson.get("type") == "GeometryCollection":
                map_request_geometry_geometries = map_reqeust_geometry_geojson.get(
                    "geometries"
                )
            else:
                map_request_geometry_geometries = [map_reqeust_geometry_geojson]
            map_request_geometry_feature_collection = {
                "type":
                    "FeatureCollection",
                "features": [{
                    "type": "Feature", "geometry": feature_geometry
                } for feature_geometry in map_request_geometry_geometries]
            }
            map_request.geometry_features = map_request_geometry_feature_collection
            map_request.save()


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0030_maprequest_geometry_features'),
    ]

    operations = [
        migrations.RunPython(
            compute_geometry_features, reverse_code=migrations.RunPython.noop
        ),
    ]
