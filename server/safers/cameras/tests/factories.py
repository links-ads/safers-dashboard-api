from random import random
import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.cameras.models import Camera, CameraMedia

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class CameraFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Camera

    name = FactoryFaker("word")
    last_update = FactoryFaker("date_time_this_month")
    description = optional_declaration(FactoryFaker("text"), chance=50)

    geometry = FactoryFaker("point")


class CameraMediaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CameraMedia

    timestamp = FactoryFaker("date_time_this_month")
    description = optional_declaration(FactoryFaker("text"), chance=50)

    geometry = FactoryFaker("point")

    camera = factory.SubFactory(CameraFactory)
