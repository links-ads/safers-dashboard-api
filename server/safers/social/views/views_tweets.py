import requests
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.gis import geos
from django.utils import timezone

from rest_framework import status, views
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.authentication import TokenAuthentication

from safers.users.permissions import IsRemote

from safers.social.models import Tweet
from safers.social.serializers import TweetSerializer, TweetViewSerializer


_tweets_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    example={
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [5.3805535, 43.28032785]
                },
                "properties": {
                    "tweet_id": "1526291911878713344",
                    "timestamp": "2022-05-16T20:02:03+00:00",
                    "text": "Faits divers : un mort dans l'incendie d'un appartement à Marseille - 20 Minutes https://t.co/MowahsbiPd #family #life #followforfollow"
                },
            }
        ]
    }
)  # yapf: disable


class TweetView(views.APIView):
    """
    Takes events from social media module and returns individual tweets
    """

    permission_classes = [IsAuthenticated, IsRemote]

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

        if data.pop("default_bbox") and "bbox" not in data:
            user = self.request.user
            data["bbox"] = user.default_aoi.geometry.extent

        return data

    @swagger_auto_schema(
        query_serializer=TweetViewSerializer,
        responses={status.HTTP_200_OK: _tweets_schema},
    )
    def get(self, request, *args, **kwargs):
        """
        Return all tweets
        """

        GATEWAY_URL_PATH = "/api/services/app/Social/GetEvents"

        view_serializer = TweetViewSerializer(
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
            proxy_params["NorthEast"] = (max_y, max_x)
            proxy_params["SouthWest"] = (min_y, min_x)

        try:
            response = requests.get(
                urljoin(settings.SAFERS_GATEWAY_URL, GATEWAY_URL_PATH),
                auth=TokenAuthentication(request.auth),
                params=proxy_params,
            )
            response.raise_for_status()
        except Exception as e:
            raise APIException(e)

        tweets = [
            Tweet(
                tweet_id=tweet.get("id_str"),
                timestamp=tweet.get("created_at"),
                text=tweet.get("text"),
                geometry=geos.Point(
                    event["hotspots_centroid"]["coordinates"]
                ) if event.get("hotspots_centroid") else None,            )
            for event in response.json()["items"]
            for tweet in event.get("tweets", [])
        ]  # yapf: disable
        model_serializer = TweetSerializer(
            tweets, context=self.get_serializer_context(), many=True
        )

        return Response(data=model_serializer.data, status=status.HTTP_200_OK)


"""
SAMPLE PROXY DATA SHAPE:
{
  'items': [
    {
      'activated_at': '2022-05-16T13:50:00+00:00',
      'ended_at': None,
      'hazard_id': 11,
      'hotspots': {
        'coordinates': [
          [
            [
              [ 1, 2],
              [ 3, 4],
            ]
          ]
        ],
        'type': 'MultiPolygon'
      },
      'hotspots_centroid': {
        'coordinates': [1, 2],
        'type': 'Point'
      },
      'id': 83351,
      'impact_estimation': None,
      'lang': 'fr',
      'last_impact_estimation_at': None,
      'name': 'Incendies à Marseille',
      'started_at': '2022-05-16T13:15:11+00:00',
      'total_area': {
        'coordinates': [
          [
            [
              [1, 2],
              [3, 4],
            ]
          ]
        ],
        'type': 'MultiPolygon'
      },
      'tracking_stopped_at': None,
      'tweets': [
        {
          'created_at': '2022-05-16T20:02:03+00:00',
          'id': 1526291911878713344,
          'id_str': '1526291911878713344',
          'text': "Faits divers : un mort dans l'incendie d'un appartement à Marseille - 20 Minutes https://t.co/MowahsbiPd #family #life #followforfollow"
        }
      ],
      'updated_at': '2022-05-16T20:02:03+00:00',
      'verified': False
    }
  ],
  'next': '/api/v1/events?page=1&limit=100',
  'pages': 1,
  'prev': '/api/v1/events?page=1&limit=100',
  'total': 3
}
"""