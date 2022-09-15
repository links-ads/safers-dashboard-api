import pytest

from django.contrib.gis import geos

from safers.core.utils import *


def test_case_insensitive_choices():
    class TestChoices(CaseInsensitiveTextChoices):
        TEST = "TEST", "Test"

    assert TestChoices.find_enum("TEST") == TestChoices.TEST
    assert TestChoices.find_enum("test") == TestChoices.TEST
    assert TestChoices.find_enum("TeSt") == TestChoices.TEST
    assert TestChoices.find_enum("invalid") == None


def test_cap_area_to_geojson():

    CIRCLE_AREA = [{"areaDesc": "some circle", "circle": "1, 2 3"}]
    POLYGON_AREA = [{
        "areaDesc": "some polygon", "polygon": "1, 2 3, 4 5, 6 1, 2"
    }]
    POINT_AREA = [{"areaDesc": "some point", "point": "1, 2"}]
    GEOCODE_AREA = [{"areaDesc": "some geocode", "geocode": "abcde"}]

    CIRCLE_GEOMETRY = geos.Point(2, 1).buffer(3)
    POLYGON_GEOMETRY = geos.Polygon(((2, 1), (4, 3), (6, 5), (2, 1)))
    POINT_GEOMETRY = geos.Point(2, 1)

    test_circle_feature = cap_area_to_geojson(CIRCLE_AREA)
    assert test_circle_feature["features"][0]["geometry"][
        "coordinates"] == CIRCLE_GEOMETRY.coords

    test_polygon_feature = cap_area_to_geojson(POLYGON_AREA)
    assert test_polygon_feature["features"][0]["geometry"][
        "coordinates"] == POLYGON_GEOMETRY.coords

    test_point_feature = cap_area_to_geojson(POINT_AREA)
    assert test_point_feature["features"][0]["geometry"][
        "coordinates"] == POINT_GEOMETRY.coords

    with pytest.raises(ValueError):
        cap_area_to_geojson(GEOCODE_AREA)
