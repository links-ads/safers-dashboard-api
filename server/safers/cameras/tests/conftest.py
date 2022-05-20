import pytest

from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

from safers.users.serializers import UserSerializer
from safers.users.tests.factories import UserFactory
from safers.users.utils import create_knox_token

from safers.cameras.models import CameraMediaFireClass, CameraMediaTag


@pytest.fixture
def admin():
    UserModel = get_user_model()
    admin = UserModel.objects.create_superuser(
        "admin", "admin@admin.com", "password"
    )
    # admin.verify()
    return admin


@pytest.fixture
def user():
    user = UserFactory()
    return user


@pytest.fixture
def api_client():
    """
    returns a DRF API client w/ a pre-authenticated user
    """
    def _api_client(user):
        token_dataclass = create_knox_token(None, user, None)
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_dataclass.key}",
            HTTP_ORIGIN="http://localhost"
        )
        return client

    return _api_client


@pytest.fixture
def user_data():
    """
    Provides a dictionary of user data.
    """

    # rather than use `.build()`, I actually create and then delete the model
    # this is so that the related profile can be created as well

    user = UserFactory(avatar=None)
    serializer = UserSerializer(user)
    data = serializer.data
    data["password"] = user.raw_password

    user.delete()

    return data


@pytest.fixture
def camera_fire_classes():
    """
    create the default set of fire_classes
    """
    FIRE_CLASSES_DATA = [
        {
            "name": "CL1",
            "description": "fires involving wood/plants",
        },
        {
            "name": "CL2",
            "description": "fires involving flammable materials/liquids",
        },
        {
            "name": "CL3",
            "description": "fires involving gas",
        },
    ]
    fire_classes = [
        CameraMediaFireClass.objects.get_or_create(
            name=data.pop("name"), defaults=data
        )[0] for data in FIRE_CLASSES_DATA
    ]
    return fire_classes


@pytest.fixture
def camera_tags():
    """
    create the default set of tags
    """
    TAGS_DATA = [
        {
            "name": "fire",
            "description": None,
        },
        {
            "name": "smoke",
            "description": None,
        },
    ]
    tags = [
        CameraMediaTag.objects.get_or_create(
            name=data.pop("name"), defaults=data
        )[0] for data in TAGS_DATA
    ]
    return tags
