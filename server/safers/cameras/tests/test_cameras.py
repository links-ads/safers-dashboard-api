import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status

from safers.core.tests.factories import *
from safers.cameras.tests.factories import *


@pytest.mark.django_db
class TestCameraViews:
    def test_bbox_filter(self, user, api_client):

        camera_media = CameraMediaFactory()
        (xmin, ymin, xmax, ymax) = camera_media.geometry.extent

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
        url = f"{reverse('cameras_media-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 1

        url_params = urllib.parse.urlencode({
            "geometry__bboverlaps": ",".join(map(str, out_bounding_box))
        })
        url = f"{reverse('cameras_media-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 0

    def test_favorite_camera_media(self, user, api_client, safers_settings):

        safers_settings.max_favorite_camera_media = 1
        safers_settings.save()

        camera_media = CameraMediaFactory()

        client = api_client(user)
        url = reverse("cameras_media-favorite", args=[camera_media.id])
        response = client.post(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert content["favorite"] == True

        assert camera_media in user.favorite_camera_medias.all()

    def test_unfavorite_camera_media(self, user, api_client, safers_settings):

        safers_settings.max_favorite_camera_media = 1
        safers_settings.save()

        camera_media = CameraMediaFactory()
        user.favorite_camera_medias.add(camera_media)

        client = api_client(user)
        url = reverse("cameras_media-favorite", args=[camera_media.id])
        response = client.post(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert content["favorite"] == False

        assert camera_media not in user.favorite_camera_medias.all()

    def test_cannot_favorite_camera_media(
        self, user, api_client, safers_settings
    ):

        safers_settings.max_favorite_camera_media = 1
        safers_settings.save()

        cameras_media = [CameraMediaFactory() for _ in range(2)]
        user.favorite_camera_medias.add(cameras_media[0])

        client = api_client(user)
        url = reverse("cameras_media-favorite", args=[cameras_media[1].id])
        response = client.post(url, format="json")
        assert status.is_client_error(response.status_code)
