import pytest

from django.urls import resolve, reverse

from rest_framework import status
from rest_framework.test import APIClient

from safers.users.models import User, UserProfile

from .factories import *


@pytest.mark.django_db
class TestAuthRegister:
    def test_profile_fields(self):
        """
        tests that I can get a user
        """
        role = RoleFactory()
        organization = OrganizationFactory()

        test_data = {
            "email": "test@example.com",
            "first_name": "test1",
            "last_name": "test2",
            "password": "RandomPassword123",
            "role": str(role.id),
            "organization": str(organization.id),
            "accepted_terms": True,
        }

        client = APIClient()
        url = reverse("rest_register")
        response = client.post(url, data=test_data, format="json")
        assert status.is_success(response.status_code)

        user_data = response.json()
        user = User.objects.get(email=test_data["email"])
        user_profile = user.profile

        # just test some random fields match...
        assert user_data["user"]["email"] == test_data["email"] == user.email
        assert user_data["user"]["first_name"] == test_data[
            "first_name"] == user_profile.first_name
