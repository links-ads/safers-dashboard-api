from collections import OrderedDict

from django.conf import settings

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import viewsets

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.tasks.serializers import MessageSerializer
from safers.tasks.utils import get_task


class PublishMessageView(GenericAPIView):

    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    # @swagger_auto_schema(
    #     request_body=openapi.Schema(
    #         type=openapi.TYPE_OBJECT,
    #         example={
    #             "message_id": "string",
    #             "app_id": "string",
    #             "payload": {
    #                 "a": "bunch",
    #                 "of": "JSON",
    #             }
    #         },
    #     ),
    #     responses={status.HTTP_200_OK: MessageSerializer},
    # )
    def post(self, request, *args, **kwargs):

        message_serializer = self.get_serializer(data=request.data)
        message_serializer.is_valid(raise_exception=True)
        message_data = message_serializer.data

        publish_message_task = get_task("safers.*.publish_message")
        publish_message_task(message_data)

        return Response(
            {
                "detail":
                    f"published message to {settings.CELERY_DEFAULT_QUEUE_NAME} queue",
                "message":
                    message_data
            },
            status=status.HTTP_200_OK,
        )
