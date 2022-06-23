import json

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.viewsets import ReadOnlyModelViewSet

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake

from safers.rmq import RMQ
from safers.rmq.models import Message
from safers.rmq.serializers import MessageSerializer


class MessageViewSet(ReadOnlyModelViewSet):

    permission_classes = [AllowAny]
    serializer_class = MessageSerializer

    @swagger_fake(Message.objects.none())
    def get_queryset(self):
        return Message.objects.all()

    @action(detail=False, methods=["post"])
    @swagger_auto_schema(responses={status.HTTP_200_OK: MessageSerializer})
    def publish(self, request, *args, **kwargs):
        """
        For development purposes only.
        Allows me to manually publish a message to the queue.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        try:

            rmq = RMQ()
            rmq.publish(
                json.dumps(message.body, cls=JSONEncoder),
                message.routing_key,
                str(message.id),
            )

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            raise ValidationError(e)
