import factory
from factory.faker import (
    Faker as FactoryFaker,
)  # note I use FactoryBoy's wrapper of Faker when defining factory fields
from faker import Faker
from datetime import timedelta

from django.utils import timezone

from safers.core.tests.providers import GeometryProvider
from safers.core.tests.utils import optional_declaration

from safers.cameras.models import Camera, CameraMedia, CameraMediaType

fake = Faker()

FactoryFaker.add_provider(GeometryProvider)


class CameraFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Camera

    name = FactoryFaker("word")
    model = FactoryFaker("word")
    owner = FactoryFaker("word")
    nation = FactoryFaker("country")

    altitude = FactoryFaker("pyfloat", min_value=1, max_value=500)
    direction = FactoryFaker("pyfloat", min_value=0, max_value=360)

    geometry = FactoryFaker("point")

    @factory.lazy_attribute
    def camera_id(self):
        return f"{self.owner}_{self.name}_{self.direction:03}"


class CameraMediaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CameraMedia

    camera = factory.SubFactory(CameraFactory)

    type = CameraMediaType.IMAGE
    timestamp = FactoryFaker(
        "date_time_between", start_date=timezone.now() - timedelta(days=1)
    )  # default timestamp is recent enough to match default filters
    description = optional_declaration(FactoryFaker("text"), chance=50)
    remote_url = FactoryFaker("uri")
    # direction = None
    # distance = None
    # geometry = None

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)

    @factory.post_generation
    def fire_classes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for fire_class in extracted:
                self.fire_classes.add(fire_class)
