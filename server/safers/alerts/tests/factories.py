from random import random
import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.alerts.models import Alert

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class AlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Alert

    timestamp = FactoryFaker("date_time_this_month")
    description = optional_declaration(FactoryFaker("text"), chance=50)
    source = FactoryFaker("word")

    geometry = FactoryFaker("polygon")

    @factory.lazy_attribute
    def media(self):
        return [fake.url() for _ in range(2)]
