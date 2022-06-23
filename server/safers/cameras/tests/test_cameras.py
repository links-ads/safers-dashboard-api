import pytest
import re
import urllib

from datetime import timedelta
from faker import Faker

from django.urls import resolve, reverse
from django.utils import timezone

from rest_framework import status

from safers.alerts.models import Alert

from safers.core.tests.factories import *

from safers.cameras.models import Camera, CameraMedia, CameraMediaFireClass, CameraMediaTag
from safers.cameras.tests.factories import CameraFactory, CameraMediaFactory
from safers.cameras.utils import FIRE_CLASS_MAP, TAG_MAP, process_messages

fake = Faker()


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


@pytest.mark.django_db
class TestRMQ:

    _FIRE_CLASSES_MAP = {v: k for k, v in FIRE_CLASS_MAP.items()}
    _TAG_MAP = {v: k for k, v in TAG_MAP.items()}

    def _build_message_body(self, **kwargs):
        camera = kwargs.get("camera", None)
        timestamp = kwargs.get("timestamp", timezone.now().isoformat())
        url = kwargs.get("url", fake.uri())
        fire_classes = kwargs.get("fire_classes", [])
        tags = kwargs.get("tags", [])

        assert camera is not None, "missing camera"

        message_body = {
            "timestamp": timestamp,
            "camera": {
                "ID": camera.camera_id,
                "owner": camera.owner,
                "cam_direction": camera.direction,
                "altitude": camera.altitude,
                "model": camera.model,
                # "type": camera.model,
                "latitude": camera.geometry.coords[1],
                "longitude": camera.geometry.coords[0],
            },
            "detection": {},
            "class_of_fire": {},
            "fire_location": {
                "not_available": False,
                "direction": None,
                "distance": None,
                "latitude": None,
                "longitude": None
            },
            "link": url,
        }  # yapf: disable

        if not tags:
            message_body["detection"].update({
                "not_available": True,
                "fire": False,
                "smoke": False,
            })
        else:
            message_body["detection"]["not_available"] = False
            message_body["detection"].update({
                self._TAG_MAP[tag.name]: True
                for tag in tags
            })

        if not fire_classes:
            message_body["class_of_fire"].update({
                "not_available": True,
                "class_1": False,
                "class_2": False,
                "class_3": False,
            })
        else:
            message_body["class_of_fire"]["not_available"] = False
            message_body["class_of_fire"].update({
                self._FIRE_CLASSES_MAP[fire_class.name]: True
                for fire_class in fire_classes
            })

        return message_body

    def test_create_camera_media(self, camera_fire_classes, camera_tags):

        camera = CameraFactory()

        assert CameraMedia.objects.count() == 0
        assert CameraMediaFireClass.objects.count() > 0
        assert CameraMediaTag.objects.count() > 0

        test_message = self._build_message_body(
            camera=camera,
            fire_classes=CameraMediaFireClass.objects.none(),
            tags=CameraMediaTag.objects.none(),
        )

        details = process_messages(test_message)
        camera_media_id = re.match(
            "^.*CameraMedia object \((.+)\)$", details["detail"][0]
        ).groups()[0]
        camera_media = CameraMedia.objects.get(id=camera_media_id)

        assert CameraMedia.objects.count() == 1
        assert camera_media.fire_classes.count() == 0
        assert camera_media.tags.count() == 0

        assert Alert.objects.count() == 0

    def test_create_camera_alert(self, camera_fire_classes, camera_tags):

        camera = CameraFactory()

        assert CameraMedia.objects.count() == 0
        assert CameraMediaFireClass.objects.count() > 0
        assert CameraMediaTag.objects.count() > 0

        test_message = self._build_message_body(
            camera=camera,
            fire_classes=CameraMediaFireClass.objects.filter(name="CL1"),
            tags=CameraMediaTag.objects.filter(name="fire"),
        )

        details = process_messages(test_message)
        camera_media_id = re.match(
            "^.*CameraMedia object \((.+)\)$", details["detail"][0]
        ).groups()[0]
        camera_media = CameraMedia.objects.get(id=camera_media_id)

        assert CameraMedia.objects.count() == 1
        assert "CL1" in camera_media.fire_classes.values_list("name", flat=True)
        assert "fire" in camera_media.tags.values_list("name", flat=True)

        assert Alert.objects.count() == 1
        assert len(details["detail"]) == 2

    def test_create_additional_camera_alerts(
        self, camera_fire_classes, camera_tags
    ):

        camera = CameraFactory()

        TODAY = timezone.now()
        TOMORROW = TODAY + timedelta(days=1)
        AFTER_TOMORROW = TODAY + timedelta(days=4)

        test_message_1 = self._build_message_body(
            camera=camera,
            timestamp=TODAY.isoformat(),
            fire_classes=CameraMediaFireClass.objects.filter(name="CL1"),
            tags=CameraMediaTag.objects.filter(name="fire"),
        )

        details = process_messages(test_message_1)
        assert len(details["detail"]) == 2

        assert CameraMedia.objects.count() == 1
        assert Alert.objects.count() == 1

        test_message_2 = self._build_message_body(
            camera=camera,
            timestamp=TOMORROW.isoformat(),
            fire_classes=CameraMediaFireClass.objects.filter(name="CL1"),
            tags=CameraMediaTag.objects.filter(name="fire"),
        )

        details = process_messages(test_message_2)
        assert len(details["detail"]) == 1

        assert CameraMedia.objects.count() == 2
        assert Alert.objects.count() == 1

        test_message_3 = self._build_message_body(
            camera=camera,
            timestamp=AFTER_TOMORROW.isoformat(),
            fire_classes=CameraMediaFireClass.objects.filter(name="CL1"),
            tags=CameraMediaTag.objects.filter(name="fire"),
        )

        details = process_messages(test_message_3)
        assert len(details["detail"]) == 2

        assert CameraMedia.objects.count() == 3
        assert Alert.objects.count() == 2
