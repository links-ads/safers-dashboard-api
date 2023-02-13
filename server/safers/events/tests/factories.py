from random import random
import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.events.models import Event

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    start_date = FactoryFaker("date_time_this_month")
    description = optional_declaration(FactoryFaker("text"), chance=50)
    people_affected = FactoryFaker("pyint", min_value=0, max_value=100)
    causalties = FactoryFaker("pyint", min_value=0, max_value=100)
    estimated_damage = FactoryFaker("pyfloat", min_value=0, max_value=100000)

    @factory.post_generation
    def alerts(obj, create, extracted, **kwargs):

        from safers.alerts.tests.factories import AlertFactory

        if not create:
            return

        if extracted:
            for alert in extracted:
                obj.alerts.add(alert)
        else:
            # by default add 1 alert (b/c an event w/out any alerts makes no sense)
            # (and will cause other fns to fail eventually)
            alert = AlertFactory()
            obj.alerts.add(alert)
