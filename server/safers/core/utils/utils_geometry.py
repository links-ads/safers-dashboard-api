import re

from django.contrib.gis import geos


def cap_area_to_geojson(cap_area):
    """
    Converts the area of a CAP Alert to a GEOSGeometry.
    The format of the alert area is:
        "area": [
            {
                "areaDesc": "some circle",
                "circle" : "lat, lon radius"
            },
            {
                "areaDesc": "some polygon",
                "polygon" : "lat1, lon1 lat2, lon2... latN, lonN lat1, lon1"
            },
            {
                "areaDesc": "some point",
                "point" : "lat, lon"
            },
        ]
    """

    list_of_coords_regex = re.compile(r"(?<![,\s])\s+")

    features = []
    for area in cap_area:

        feature = {
            "type": "Feature",
            "properties": {
                "description": area.get("areaDesc")
            }
        }

        if "circle" in area:
            coords, radius = list_of_coords_regex.split(area["circle"])
            lat, lon = list(map(float, coords.split(",")))
            geometry = geos.Point(lon, lat).buffer(float(radius))
            feature["geometry"] = {
                "type": "Polygon", "coordinates": geometry.coords
            }

        elif "polygon" in area:
            coords = list_of_coords_regex.split(area["polygon"])
            remapped_coords = list(
                map(lambda x: list(map(float, x.split(",")[::-1])), coords)
            )  # convert list of strings w/ commas to list of (reversed) lists
            geometry = geos.Polygon(remapped_coords)
            feature["geometry"] = {
                "type": "Polygon", "coordinates": geometry.coords
            }

        elif "point" in area:
            lat, lon = list(map(float, area["point"].split(",")))
            geometry = geos.Point(lon, lat)
            feature["geometry"] = {
                "type": "Point", "coordinates": geometry.coords
            }

        elif "geocode" in area:
            raise ValueError("SAFERS does not support alerts w/ 'geocode'.")

        else:
            raise ValueError(f"Unknown alert area type: {area}")

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }
