import pytest

from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

from safers.users.serializers import UserSerializer
from safers.users.tests.factories import UserFactory
from safers.users.utils import create_knox_token


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
