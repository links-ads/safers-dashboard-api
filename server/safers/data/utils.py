import math

from safers.data.constants import METERS_TO_KILOMETERS, CIRCUMFERENCE_OF_EARTH
# geometry fields are in WGS84 as per https://docs.djangoproject.com/en/4.1/ref/contrib/gis/model-api/#srid


def meters_to_degrees(meters, latitude=None):
    """
    takes a geometric distance in meters and converts to degrees
    (which is what WGS84 expects); if latitude is not None
    then a more precise calculation is used taking into account 
    distance from the equator
    """

    kilometers = meters * METERS_TO_KILOMETERS
    degrees = kilometers / CIRCUMFERENCE_OF_EARTH * 360.0
    if latitude is not None:
        degrees /= math.cos(latitude / 360.0 * math.pi)
    return degrees
