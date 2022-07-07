import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.data.models import DataType, MapRequest

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class DataTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DataType

    group = FactoryFaker("word")
    subgroup = FactoryFaker("word")
    format = FactoryFaker("word")

    description = optional_declaration(FactoryFaker("text"), chance=50)
    info = optional_declaration(FactoryFaker("text"), chance=50)

    @factory.lazy_attribute_sequence
    def datatype_id(self, n):
        return f"data_type_{n}"


class MapRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MapRequest

    user = None  # user is set in tests as needed
    title = FactoryFaker("sentence")
    # status = MapRequestStatus.PROCESSING
    parameters = FactoryFaker(
        "pydict", nb_elements=4, value_types=["str", "int", "bool"]
    )
    geometry = FactoryFaker("polygon")

    @factory.post_generation
    def data_types(obj, create, extracted, **kwargs):

        if not create:
            return

        if extracted:
            for data_type in extracted:
                obj.data_types.add(data_type)
