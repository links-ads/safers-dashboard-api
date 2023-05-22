import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker
from faker import Faker

from django.db.models.signals import post_save

from safers.core.tests.utils import optional_declaration

from safers.aois.tests.factories import AoiFactory

from safers.users.models import User, UserProfile
from safers.users.tests.utils import generate_password


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    first_name = FactoryFaker("first_name")
    last_name = FactoryFaker("last_name")
    company = FactoryFaker("company")
    address = FactoryFaker("street_address")
    city = FactoryFaker("city")
    country = FactoryFaker("country")

    user = factory.SubFactory(
        "safers.users.tests.factories.UserFactory", profile=None
    )


@factory.django.mute_signals(
    post_save
)  # prevent signals from trying to create a profile outside of this factory
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ["email"]

    email = FactoryFaker("email")

    default_aoi = factory.SubFactory("safers.aois.tests.factories.AoiFactory")

    @factory.lazy_attribute
    def username(self):
        return self.email

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = generate_password()
        self.raw_password = (
            password  # the instance has a "raw_password" variable to use in tests
        )
        self.set_password(password)

    # @factory.post_generation
    # def emailaddress_set(
    #     self, create: bool, extracted: Sequence[Any], **kwargs
    # ):
    #     if not create:
    #         return

    #     if extracted:
    #         # I am very unlikely to be here, creating loads of emailaddresses
    #         for emailaddress in extracted:
    #             self.emailaddress_set.add(emailaddress)

    #     else:
    #         emailaddress = EmailAddressFactory(
    #             user=self, email=self.email, primary=True, verified=False
    #         )

    profile = factory.RelatedFactory(UserProfileFactory, "user")
