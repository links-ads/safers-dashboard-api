import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.notifications.models import Notification, NotificationGeometry

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class NotificationGeometryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationGeometry

    description = FactoryFaker("sentence")
    geometry = FactoryFaker("polygon")

    notification = factory.SubFactory(
        "safers.notifications.tests.factories.NotificationFactory"
    )


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

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

    @factory.post_generation
    def geometries(obj, create, extracted, **kwargs):
        """
        If called like: NotificationFactory(geometries=N) it generates a Notification w/ N NotificationGeometries.
        If called without `geometries` argument, it generates 1 NotificationGeometry for this Notification.
        """

        if not create:
            return

        if extracted:
            for _ in range(extracted):
                NotificationGeometryFactory(notification=obj)
        else:
            NotificationGeometryFactory(notification=obj)
