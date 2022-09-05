import requests
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from rest_framework import ISO_8601, views
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated

from safers.users.authentication import ProxyAuthentication
from safers.users.permissions import IsRemote


def parse_none(value):
    """
    Many of the Proxy APIs return None as string rather than
    a null JSON value; This lil function gets around that.
    """
    return None if value == "None" else value


def parse_datetime(value):
    """
    DateTime format is a bit inconsistent in Proxy
    APIs; This lil function gets around that.
    """
    if value:
        ChatbotDateTimeFormats = [
            ISO_8601, "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"
        ]
        for datetime_format in ChatbotDateTimeFormats:
            try:
                return datetime.strptime(value, datetime_format)
            except ValueError as e:
                pass
        raise ValueError(f"Invalid datetime format for '{value}'")


class ChatbotView(views.APIView):
    """
    All the proxy chatbot API endpoints have very similar signatures;
    So this single class can be used as the basis for all chatbot views.
    """

    permission_classes = [IsAuthenticated, IsRemote]

    view_serializer_class = None
    model_serializer_class = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert self.view_serializer_class is not None
        assert self.model_serializer_class is not None

    def get_serializer_context(self):
        return {
            'request': self.request, 'format': self.format_kwarg, 'view': self
        }

    def update_default_data(self, data):

        default_date = data.pop("default_date")
        if default_date and "start" not in data:
            data["start"] = timezone.now() - settings.SAFERS_DEFAULT_TIMERANGE
        if default_date and "end" not in data:
            data["end"] = timezone.now()

        default_bbox = data.pop("default_bbox")
        if default_bbox and "bbox" not in data:
            user = self.request.user
            data["bbox"] = user.default_aoi.geometry.extent

        return data

    def get_proxy_list_data(self, request, proxy_url=None):

        view_serializer = self.view_serializer_class(
            data=request.query_params,
            context=self.get_serializer_context(),
        )
        view_serializer.is_valid(raise_exception=True)

        updated_data = self.update_default_data(view_serializer.validated_data)
        proxy_params = {
            view_serializer.ProxyFieldMapping[k]: v
            for k, v in updated_data.items()
            if k in view_serializer.ProxyFieldMapping
        }  # yapf: disable
        if "bbox" in proxy_params:
            min_x, min_y, max_x, max_y = proxy_params.pop("bbox")
            proxy_params["NorthEastBoundary.Latitude"] = max_y
            proxy_params["NorthEastBoundary.Longitude"] = max_x
            proxy_params["SouthWestBoundary.Latitude"] = min_y
            proxy_params["SouthWestBoundary.Longitude"] = min_x

        try:
            response = requests.get(
                proxy_url,
                auth=ProxyAuthentication(request.user),
                params=proxy_params,
                timeout=4,  # 4 seconds as per https://requests.readthedocs.io/en/stable/user/advanced/#timeouts
            )  # yapf: disable
            response.raise_for_status()
        except Exception as e:
            raise APIException(e)

        return response.json()["data"]
