import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status

from safers.data.tests.factories import *


@pytest.mark.django_db
class TestMapRequests:
    def test_request_id(self):

        map_request_1 = MapRequestFactory()
        assert map_request_1.request_id == "1"

        map_request_2 = MapRequestFactory()
        assert map_request_2.request_id == "2"

        MapRequest.objects.all().delete()

        map_request_3 = MapRequestFactory()
        assert map_request_3.request_id == "3"
