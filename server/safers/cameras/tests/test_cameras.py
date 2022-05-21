import pytest
import urllib

from datetime import timedelta

from django.urls import resolve, reverse
from django.utils import timezone

from rest_framework import status

from safers.core.tests.factories import *

from safers.cameras.models import CameraMediaTag
from safers.cameras.tests.factories import *


@pytest.mark.django_db
class TestCameraModel:
    def test_last_update(self):

        camera = CameraFactory()

        assert camera.last_update is None

        TODAY = timezone.now()
        YESTERDAY = TODAY - timedelta(days=1)
        BEFORE_YESTERDAY = TODAY - timedelta(days=2)

        before_yesterday_camera_media = CameraMediaFactory(
            timestamp=BEFORE_YESTERDAY, camera=camera
        )
        camera.refresh_from_db()
        assert camera.last_update == BEFORE_YESTERDAY

        today_camera_media = CameraMediaFactory(timestamp=TODAY, camera=camera)
        camera.refresh_from_db()
        assert camera.last_update == TODAY

        yesterday_camera_media = CameraMediaFactory(
            timestamp=YESTERDAY, camera=camera
        )
        camera.refresh_from_db()
        assert camera.last_update == TODAY

        today_camera_media.delete()
        camera.refresh_from_db()
        assert camera.last_update == YESTERDAY

        yesterday_camera_media.delete()
        camera.refresh_from_db()
        assert camera.last_update == BEFORE_YESTERDAY

        before_yesterday_camera_media.delete()
        camera.refresh_from_db()
        assert camera.last_update is None


@pytest.mark.django_db
class TestCameraMediaModel:
    def test_filters(self):

        camera = CameraFactory()
        camera_media = [
            CameraMediaFactory(description=f"camera {i}", camera=camera)
            for i in range(4)
        ]

        fire_tag, _ = CameraMediaTag.objects.get_or_create(name="fire")
        smoke_tag, _ = CameraMediaTag.objects.get_or_create(name="smoke")

        camera_media[0]  # undetected
        camera_media[1].tags.add(fire_tag)
        camera_media[2].tags.add(smoke_tag)
        camera_media[3].tags.add(fire_tag, smoke_tag)

        undetected_media = CameraMedia.objects.undetected()
        detected_media = CameraMedia.objects.detected()
        fire_media = CameraMedia.objects.fire()
        smoke_media = CameraMedia.objects.smoke()

        assert len(undetected_media) == 1
        assert camera_media[0] in undetected_media

        assert len(detected_media) == 3
        assert camera_media[1] in detected_media and camera_media[
            2] in detected_media and camera_media[3] in detected_media

        assert len(fire_media) == 2
        assert camera_media[1] in fire_media and camera_media[3] in fire_media

        assert len(smoke_media) == 2
        assert camera_media[2] in smoke_media and camera_media[3] in smoke_media


@pytest.mark.django_db
class TestCameraMediaView:
    def test_bbox_filter(self, user, api_client):

        camera_media = CameraMediaFactory(camera=CameraFactory())
        (xmin, ymin, xmax, ymax) = camera_media.camera.geometry.buffer(
            Camera.MIN_BOUNDING_BOX_SIZE
        ).extent

        client = api_client(user)

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
        url = f"{reverse('cameras_media-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 1

        url_params = urllib.parse.urlencode({
            "bbox": ",".join(map(str, out_bounding_box))
        })
        url = f"{reverse('cameras_media-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 0

    def test_tags_filter(self, user, api_client):

        fire_tag, _ = CameraMediaTag.objects.get_or_create(name="fire")
        smoke_tag, _ = CameraMediaTag.objects.get_or_create(name="smoke")
        camera_media = CameraMediaFactory(camera=CameraFactory())

        client = api_client(user)
        url = reverse("cameras_media-list")

        camera_media.tags.clear()  # fire,smoke doesn't match
        response = client.get(
            f"{url}?default_bbox=false&tags=fire,smoke", format="json"
        )
        assert status.is_success(response.status_code)
        content = response.json()
        assert len(content) == 0

        camera_media.tags.add(fire_tag)  # fire,smoke matches 1
        response = client.get(
            f"{url}?default_bbox=false&tags=fire,smoke", format="json"
        )
        assert status.is_success(response.status_code)
        content = response.json()
        assert len(content) == 1

        camera_media.tags.add(fire_tag)  # fire matches 1
        response = client.get(
            f"{url}?default_bbox=false&tags=fire", format="json"
        )
        assert status.is_success(response.status_code)
        content = response.json()
        assert len(content) == 1

        camera_media.tags.add(smoke_tag)  # smoke matches 1
        response = client.get(
            f"{url}?default_bbox=false&tags=smoke", format="json"
        )
        assert status.is_success(response.status_code)
        content = response.json()
        assert len(content) == 1
