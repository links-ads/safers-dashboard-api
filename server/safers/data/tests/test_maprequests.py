import pytest

from django.urls import resolve, reverse

from rest_framework import status

from safers.data.tests.factories import *
from safers.data.models.models_maprequests import MapRequestStatus


@pytest.mark.django_db
class TestMapRequests:
    def test_generate_request_id(self):

        map_request_1 = MapRequestFactory()
        assert map_request_1.request_id == "1"

        map_request_2 = MapRequestFactory()
        assert map_request_2.request_id == "2"

        MapRequest.objects.all().delete()

        map_request_3 = MapRequestFactory()
        assert map_request_3.request_id == "3"

    def test_process_message(self, mock_method):
        data_type = DataTypeFactory(is_on_demand=True)
        map_request = MapRequestFactory(data_types=[data_type])
        map_request_data_type = map_request.map_request_data_types.first()

        assert map_request_data_type.status is None

        method = mock_method(
            routing_key=
            f"status.dsh.{data_type.datatype_id}.astro.{map_request.request_id}"
        )

        message_body = {
            "type": "start",
            "status_code": 200,
        }
        MapRequest.process_message(message_body, method=method)
        assert map_request.map_request_data_types.count() == 1
        map_request_data_type.refresh_from_db()
        assert map_request_data_type.status == MapRequestStatus.PROCESSING

        message_body = {
            "type": "end",
            "status_code": 200,
        }
        MapRequest.process_message(message_body, method=method)
        assert map_request.map_request_data_types.count() == 1
        map_request_data_type.refresh_from_db()
        assert map_request_data_type.status == MapRequestStatus.AVAILABLE

        message_body = {
            "type": "error",
            "status_code": 500,
        }
        MapRequest.process_message(message_body, method=method)
        assert map_request.map_request_data_types.count() == 1
        map_request_data_type.refresh_from_db()
        assert map_request_data_type.status == MapRequestStatus.FAILED
