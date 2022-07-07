import pytest
import uuid

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
def local_user():
    user = UserFactory()
    return user


@pytest.fixture
def remote_user():
    user = UserFactory()
    # pretend there is an associated auth_id for the Oauth2User
    user.auth_id = str(uuid.uuid4())
    user.save()
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
