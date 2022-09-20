import pytest

from django.urls import resolve, reverse

from rest_framework import status

from safers.data.tests.factories import *
from safers.data.models.models_maprequests import MapRequestStatus
from safers.data.serializers.serializers_maprequest import MapRequestSerializer


@pytest.mark.django_db
class TestMapRequests:
    def test_group_map_requests(self):
        """
        tests that the output of MapRequestListSerializer is grouped by category
        """

        data_types = [
            DataTypeFactory(datatype_id=f"{i}", group=f"group_{i}")
            for i in range(3)
        ]
        map_requests = [
            MapRequestFactory(
                title=f"map_request_{i}", data_types=[data_types[i % 3]]
            ) for i in range(6)
        ]

        serializer = MapRequestSerializer(map_requests, many=True)
        content = serializer.data

        assert len(content) == 3
        for i in in range(3):
            assert content[i]["title"] == data_types[i].group.title()
            assert len(content["children"]) == 2
          
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

        SUCCESS_MESSAGE = "success"
        FAILURE_MESSAGE = "failure"

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
            "message": SUCCESS_MESSAGE,
        }
        MapRequest.process_message(message_body, method=method)
        assert map_request.map_request_data_types.count() == 1
        map_request_data_type.refresh_from_db()
        assert map_request_data_type.status == MapRequestStatus.AVAILABLE
        assert map_request_data_type.message == SUCCESS_MESSAGE

        message_body = {
            "type": "error",
            "status_code": 500,
            "message": FAILURE_MESSAGE,
        }
        MapRequest.process_message(message_body, method=method)
        assert map_request.map_request_data_types.count() == 1
        map_request_data_type.refresh_from_db()
        assert map_request_data_type.status == MapRequestStatus.FAILED
        assert map_request_data_type.message == FAILURE_MESSAGE
