import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields

from django.core.files.uploadedfile import SimpleUploadedFile

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.aois.models import Aoi

FactoryFaker.add_provider(GeometryProvider)


class AoiFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Aoi

    name = FactoryFaker("word")
    description = optional_declaration(FactoryFaker("text"), chance=50)
    geometry = FactoryFaker("polygon")
