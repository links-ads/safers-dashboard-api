import pytest
import uuid

from faker import Faker

from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

from safers.data.models.models_maprequests import get_next_request_id

from safers.rmq import RMQ

from safers.users.tests.factories import UserFactory
from safers.users.utils import create_knox_token

fake = Faker()


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


@pytest.fixture
def mock_method():
    """
    returns a mock object w/ just enough content to act as a Pika Method
    (just need something w/ a `routing_key`)
    """

    rmq = RMQ()

    class _method(object):
        def __init__(self, *args, **kwargs):
            self.routing_key = kwargs.get("routing_key")

    def _mock_method(routing_key=None):

        if not routing_key:
            routing_key = f"status.{rmq.config.app_id}.{fake.pyint()}.{rmq.config.username}.{get_next_request_id()}"

        return _method(routing_key=routing_key)

    return _mock_method
