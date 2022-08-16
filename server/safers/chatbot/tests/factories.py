from datetime import timedelta
from random import randint

import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from django.utils import timezone

from safers.core.tests.providers import GeometryProvider

from safers.chatbot.models import Communication, Action, ActionStatusTypes

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class CommunicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Communication

    # source_organization

    start_inclusive = FactoryFaker("pybool")
    end_inclusive = FactoryFaker("pybool")

    # scope
    # restriction
    # target_organizations

    message = FactoryFaker("sentence")

    geometry = FactoryFaker("point")

    @factory.lazy_attribute
    def start(self):
        # random date last month
        delta = timedelta(days=31)
        return fake.date_time_this_month() - delta

    @factory.lazy_attribute
    def end(self):
        # random date either before or after now
        now = timezone.now()
        delta = timedelta(days=1)
        ongoing = randint(0, 1)
        if ongoing:
            return now + delta
        else:
            return now - delta

    @factory.lazy_attribute_sequence
    def communication_id(self, n):
        return f"{n}"


class ActionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Action

    timestamp = FactoryFaker("date_time_this_month")
    activity = FactoryFaker("word")
    username = FactoryFaker("word")
    organization = FactoryFaker("word")
    # source

    status = FactoryFaker(
        "random_element", elements=ActionStatusTypes.values + [None]
    )

    geometry = FactoryFaker("point")

    @factory.lazy_attribute_sequence
    def action_id(self, n):
        return f"{n}"

    @factory.lazy_attribute
    def activity(self):
        # only set an activity if status is ACTIVE
        if self.status == ActionStatusTypes.ACTIVE:
            return fake.word()
