from datetime import timedelta
from random import randint

import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker

from django.utils import timezone

from safers.core.tests.providers import GeometryProvider

from safers.chatbot.models import Action, ActionStatusTypes, Communication, Mission, MissionStatusTypes, Report, ReportContentTypes,  ReportStatusTypes

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report

    timestamp = FactoryFaker("date_time_this_month")
    status = FactoryFaker("random_element", elements=ReportStatusTypes.values)
    content = FactoryFaker("random_element", elements=ReportContentTypes.values)

    is_public = FactoryFaker("pybool")
    description = FactoryFaker("sentence")
    geometry = FactoryFaker("point")

    @factory.lazy_attribute_sequence
    def report_id(self, n):
        return f"{n}"

    @factory.lazy_attribute
    def mission_id(self):
        return str(fake.pyint(min_value=1, max_value=10))

    @factory.lazy_attribute
    def media(self):
        return [{
            "url": fake.url(),
            "thumbnail": fake.url(),
            "type": "Image",
        } for _ in range(fake.pyint(min_value=0, max_value=4))]

    @factory.lazy_attribute
    def reporter(self):
        return {
            "name": fake.first_name(),
            "organization": fake.word(),
        }


class CommunicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Communication

    start_inclusive = FactoryFaker("pybool")
    end_inclusive = FactoryFaker("pybool")

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


class MissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mission

    description = FactoryFaker("sentence")
    username = FactoryFaker("word")
    organization = FactoryFaker("word")
    start_inclusive = FactoryFaker("pybool")
    end_inclusive = FactoryFaker("pybool")

    status = FactoryFaker(
        "random_element", elements=MissionStatusTypes.values + [None]
    )

    geometry = FactoryFaker("point")

    @factory.lazy_attribute_sequence
    def mission_id(self, n):
        return f"{n}"

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

    @factory.lazy_attribute
    def reports(self):
        report_ids = [i for i in range(fake.pyint(min_value=1, max_value=10))]
        return [{
            "id": str(report_id),
            "name": f"Report {report_id}",
        } for report_id in report_ids]
