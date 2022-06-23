import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.aois.models import Aoi

FactoryFaker.add_provider(GeometryProvider)


class AoiFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Aoi

    name = FactoryFaker("word")
    description = optional_declaration(FactoryFaker("text"), chance=50)
    country = FactoryFaker("country")
    zoom_level = FactoryFaker("pyfloat", min_value=0, max_value=12)
    midpoint = FactoryFaker("point")
    geometry = FactoryFaker("polygon")
