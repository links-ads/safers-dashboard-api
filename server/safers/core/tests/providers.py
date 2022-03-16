from copy import deepcopy
from faker import Faker
from faker.providers import BaseProvider

from django.contrib.gis.geos import Point, LineString, LinearRing, Polygon, MultiPolygon
from django.core.exceptions import ValidationError

SRID = 4326
fake = Faker()


class PrettyLoremProvider(BaseProvider):
    """
    Provides fakes for text to include "pretty" features,
    like removing trailing periods, or capitalizing things
    """
    def pretty_words(self, nb=3, ext_word_list=None):
        """
        returns a list of pretty words
        """
        words = fake.words(nb=3, ext_word_list=ext_word_list)
        return [w.title() for w in words]

    def pretty_sentence(self, nb_words=6, ext_word_list=None):
        """
        returns a string of pretty words
        """
        words = fake.words(nb=nb_words, ext_word_list=ext_word_list)
        return " ".join(map(lambda x: x.title(), words))


class GeometryProvider(BaseProvider):
    """
    Provides fakes for GeoDjango classes.
    """
    def point(self):
        coords = list(map(float, [fake.longitude(), fake.latitude()]))
        point = Point(coords, srid=SRID)
        return point

    def line_string(self, n_points=2):
        assert n_points >= 2
        points = [self.generator.point() for _ in range(n_points)]
        line_string = LineString(points, srid=SRID)
        return line_string

    def linear_ring(self, n_points=4):
        assert n_points >= 4
        points = [self.generator.point() for _ in range(n_points - 1)]
        points.append(deepcopy(points[0]))
        linear_ring = LinearRing(points, srid=SRID)
        return linear_ring

    def polygon(self, n_points=4):
        assert n_points >= 4
        linear_ring = self.generator.linear_ring(n_points=n_points)
        polygon = Polygon(linear_ring, srid=SRID)
        return polygon

    def multi_polygon(self, n_polygons=2):
        assert n_polygons >= 2
        polygons = [self.generator.polygon() for _ in range(n_polygons)]
        multi_polygon = MultiPolygon(polygons, srid=SRID)
        return multi_polygon


class ValidatedProvider(BaseProvider):
    """
    Provides fakes that exclude invalid values.
    """
    def _generate_valid_value(self, faker, validators=[], max_attempts=1000):

        attempt = 0

        while True:

            attempt += 1

            value = faker()
            try:
                validity = [validator(value) for validator in validators]
                # assume that a validator returns nothing or a truthy value if it passes
                # or a falsey value or raises an exception (below) if it fails
                if all(map(lambda x: x is None or bool(x), validity)):
                    return value
            except ValidationError:
                pass

            if attempt >= max_attempts:
                msg = f"Exceeded {attempt} attempts to generate a value from ValidatedProvider"
                raise ValidationError(msg)

    def validated_word(self, **kwargs):

        validators = kwargs.pop("validators", [])
        max_attempts = kwargs.pop("max_attempts", 1000)

        faker = lambda: fake.word(**kwargs)

        word = self._generate_valid_value(
            faker, validators=validators, max_attempts=max_attempts
        )
        return word
