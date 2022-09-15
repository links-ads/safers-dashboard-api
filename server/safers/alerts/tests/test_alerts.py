import pytest
import urllib

from datetime import timedelta

from django.conf import settings
from django.urls import resolve, reverse
from django.utils import timezone

from rest_framework import status

from .factories import *

from safers.alerts.models import Alert
from safers.events.models import Event


@pytest.mark.django_db
class TestAlertViews:
    def test_ordering_favorites(self, remote_user, api_client):

        TODAY = timezone.now()
        YESTERDAY = TODAY - timedelta(days=1)
        TOMORROW = TODAY + timedelta(days=1)

        alerts = [
            AlertFactory(timestamp=timestamp)
            for timestamp in [YESTERDAY, TODAY, TOMORROW]
        ]

        client = api_client(remote_user)
        url = f"{reverse('alerts-list')}?order=-date&default_bbox=false&default_date=false"

        response = client.get(url, format="json")
        content = response.json()
        assert status.is_success(response.status_code)

        assert content[0]["id"] == str(alerts[2].id)
        assert content[1]["id"] == str(alerts[1].id)
        assert content[2]["id"] == str(alerts[0].id)

        remote_user.favorite_alerts.add(alerts[1])

        response = client.get(url, format="json")
        content = response.json()
        assert status.is_success(response.status_code)

        assert content[0]["id"] == str(alerts[1].id)
        assert content[1]["id"] == str(alerts[2].id)
        assert content[2]["id"] == str(alerts[0].id)

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

    def test_validate_overlapping(self):

        timestamp = timezone.now()
        alert1 = AlertFactory(timestamp=timestamp, geometries=2)
        alert2 = AlertFactory(timestamp=timestamp, geometries=2)
        for alert1_geometry, alert2_geometry in zip(alert1.geometries.all(), alert2.geometries.all()):
            alert1_geometry.geometry = alert2_geometry.geometry
            alert1_geometry.save()

        assert Event.objects.count() == 0

        alert1.validate()
        assert Event.objects.count() == 1
        event = Event.objects.first()
        assert alert1 in event.alerts.all()
        assert alert2 not in event.alerts.all()

        alert2.validate()
        assert Event.objects.count() == 1
        event = Event.objects.first()
        assert alert1 in event.alerts.all()
        assert alert2 in event.alerts.all()

    def test_validate_non_overlapping(self):

        timestamp = timezone.now()
        alert1 = AlertFactory(timestamp=timestamp, geometries=2)
        alert2 = AlertFactory(
            timestamp=timestamp +
            timedelta(hours=settings.SAFERS_POSSIBLE_EVENT_TIMERANGE * 2),
            geometries=2
        )

        assert Event.objects.count() == 0

        alert1.validate()
        assert Event.objects.count() == 1
        event = Event.objects.first()
        assert alert1 in event.alerts.all()
        assert alert2 not in event.alerts.all()

        alert2.validate()
        assert Event.objects.count() == 2
        event = Event.objects.first()
        assert alert1 not in event.alerts.all()
        assert alert2 in event.alerts.all()
