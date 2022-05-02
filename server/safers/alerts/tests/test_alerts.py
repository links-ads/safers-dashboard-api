import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status

from .factories import *


@pytest.mark.django_db
class TestAlertViews:
    def test_favorite_alert(self, remote_user, api_client):
        alert = AlertFactory()

        assert alert not in remote_user.favorite_alerts.all()

        client = api_client(remote_user)
        url = reverse("alerts-favorite", kwargs={"alert_id": alert.id})

        response = client.post(url, format="json")
        assert status.is_success(response.status_code)

        assert alert in remote_user.favorite_alerts.all()

    def test_bbox_filter(self, remote_user, api_client):

        alert = AlertFactory()
        (xmin, ymin, xmax, ymax) = alert.geometries.first().geometry.extent

        client = api_client(remote_user)

        in_bounding_box = [xmin, ymin, xmax, ymax]
        out_bounding_box = [
            xmin + (xmax - xmin) + 1,
            ymin + (ymax - ymin) + 1,
            xmax + (xmax - xmin) + 1,
            ymax + (ymax - ymin) + 1,
        ]

        url_params = urllib.parse.urlencode({
            "bbox": ",".join(map(str, in_bounding_box))
        })
        url = f"{reverse('alerts-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 1

        url_params = urllib.parse.urlencode({
            "bbox": ",".join(map(str, out_bounding_box))
        })
        url = f"{reverse('alerts-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 0
