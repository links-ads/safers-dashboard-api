import json

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.viewsets import ReadOnlyModelViewSet

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
    def publish(self, request, *args, **kwargs):

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


# class PublishMessageView(GenericAPIView):
#     """
#     send a message to RMQ
#     """

#     permission_classes = [AllowAny]
#     serializer_class = MessageSerializer

#     def post(self, request, *args, **kwargs):

#         message_serializer = self.get_serializer(
#             data=request.data, context=self.get_serializer_context()
#         )
#         message_serializer.is_valid(raise_exception=True)
#         message_data = message_serializer.data

#         try:
#             routing_key = "status.test.1"
#             message_id = "test_message_id"
#             app_id = "test_app_id"

#             rmq = RMQ()
#             rmq.publish(
#                 json.dumps(message_data, cls=JSONEncoder),
#                 routing_key,
#                 message_id,
#                 app_id
#             )

#             return Response(message_data, status=status.HTTP_200_OK)

#         except Exception as e:
#             raise ValidationError(e)
