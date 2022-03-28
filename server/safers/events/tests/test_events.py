import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status

from safers.core.tests.factories import *
from safers.events.tests.factories import *


@pytest.mark.django_db
class TestEventViews:
    def test_bbox_filter(self, user, api_client):

        event = EventFactory()
        (xmin, ymin, xmax, ymax) = event.geometry.extent

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
        url = f"{reverse('events-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 1

        url_params = urllib.parse.urlencode({
            "geometry__bboverlaps": ",".join(map(str, out_bounding_box))
        })
        url = f"{reverse('events-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 0

    def test_favorite_event(self, user, api_client, safers_settings):

        safers_settings.max_favorite_events = 1
        safers_settings.save()

        event = EventFactory()

        client = api_client(user)
        url = reverse("events-favorite", args=[event.id])
        response = client.post(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert content["favorite"] == True

        assert event in user.favorite_events.all()

    def test_unfavorite_event(self, user, api_client, safers_settings):

        safers_settings.max_favorite_events = 1
        safers_settings.save()

        event = EventFactory()
        user.favorite_events.add(event)

        client = api_client(user)
        url = reverse("events-favorite", args=[event.id])
        response = client.post(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert content["favorite"] == False

        assert event not in user.favorite_events.all()

    def test_cannot_favorite_event(self, user, api_client, safers_settings):

        safers_settings.max_favorite_events = 1
        safers_settings.save()

        events = [EventFactory() for _ in range(2)]
        user.favorite_events.add(events[0])

        client = api_client(user)
        url = reverse("events-favorite", args=[events[1].id])
        response = client.post(url, format="json")
        assert status.is_client_error(response.status_code)
