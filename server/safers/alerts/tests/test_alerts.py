import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status

from .factories import *


@pytest.mark.django_db
class TestAlertViews:
    def test_bbox_filter(self, user, api_client):

        alert = AlertFactory()
        (xmin, ymin, xmax, ymax) = alert.geometry.extent

        client = api_client(user)

        in_bounding_box = [xmin, ymin, xmax, ymax]
        out_bounding_box = [
            xmin + (xmax - xmin) + 1,
            ymin + (ymax - ymin) + 1,
            xmax + (xmax - xmin) + 1,
            ymax + (ymax - ymin) + 1,
        ]

        url_params = urllib.parse.urlencode({
            "geometry__bboverlaps": ",".join(map(str, in_bounding_box))
        })
        url = f"{reverse('alerts-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 1

        url_params = urllib.parse.urlencode({
            "geometry__bboverlaps": ",".join(map(str, out_bounding_box))
        })
        url = f"{reverse('alerts-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 0
