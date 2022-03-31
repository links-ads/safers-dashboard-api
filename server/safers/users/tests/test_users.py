import pytest

from django.urls import resolve, reverse

from rest_framework import status

from safers.core.tests.utils import shuffle_string

from .factories import *


@pytest.mark.django_db
class TestUserViews:
    def test_get(self, user, api_client):
        """
        tests that I can get a user
        """

        client = api_client(user)

        url = reverse("users", args=[user.id])
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        user_data = response.json()

        # just test some random fields match...
        assert user_data["id"] == str(user.id)
        assert user_data["email"] == user.email
        assert user_data["first_name"] == user.profile.first_name

    def test_put(self, user, api_client):
        """
        tests that I can partially update a user
        """

        client = api_client(user)

        test_data = {"first_name": shuffle_string(user.profile.first_name)}

        url = reverse("users", args=[user.id])
        response = client.get(url, data=test_data, format="json")
        assert status.is_success(response.status_code)

        test_data = response.json()
        test_data["first_name"] = shuffle_string(test_data["first_name"])

        response = client.put(url, data=test_data, format="json")

        user_data = response.json()
        user.profile.refresh_from_db()

        assert test_data["first_name"] == user_data["first_name"]
        assert test_data["first_name"] == user.profile.first_name

    def test_patch(self, user, api_client):
        """
        tests that I can partially update a user
        """

        client = api_client(user)

        test_data = {"first_name": shuffle_string(user.profile.first_name)}

        url = reverse("users", args=[user.id])
        response = client.patch(url, data=test_data, format="json")
        assert status.is_success(response.status_code)

        user_data = response.json()
        user.profile.refresh_from_db()

        assert test_data["first_name"] == user_data["first_name"]
        assert test_data["first_name"] == user.profile.first_name
