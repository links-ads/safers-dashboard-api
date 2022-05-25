import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from safers.core.tests.utils import optional_declaration

from safers.data.models import DataType

fake = Faker()


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
