import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.alerts.models import Alert, AlertGeometry

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class AlertGeometryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AlertGeometry

    description = FactoryFaker("sentence")
    geometry = FactoryFaker("polygon")

    alert = factory.SubFactory("safers.alerts.tests.factories.AlertFactory")


class AlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Alert

    # type = AlertType.UNVALIDATED
    timestamp = FactoryFaker("date_time_this_month")
    status = FactoryFaker("word")
    source = FactoryFaker("word")
    scope = FactoryFaker("word")
    category = FactoryFaker("word")
    event = FactoryFaker("word")
    urgency = FactoryFaker("word")
    severity = FactoryFaker("word")
    certainty = FactoryFaker("word")
    description = FactoryFaker("sentence")
    message = FactoryFaker("pydict", value_types=["str"])

    @factory.lazy_attribute
    def media(self):
        return [fake.url() for _ in range(2)]

    @factory.post_generation
    def geometries(obj, create, extracted, **kwargs):
        """
        If called like: AlertFactory(geometries=N) it generates an Alert w/ N AlertGeometries.
        If called without `geometries` argument, it generates 1 AlertGeometry for this Alert.
        """

        if not create:
            return

        if extracted:
            for _ in range(extracted):
                AlertGeometryFactory(alert=obj)
        else:
            AlertGeometryFactory(alert=obj)
