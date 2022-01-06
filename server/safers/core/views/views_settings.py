from rest_framework import generics

from safers.core.decorators import swagger_fake
from safers.core.models import SafersSettings
from safers.core.permissions import IsAuthenticatedOrAdmin
from safers.core.serializers import SafersSettingsSerializer


class SafersSettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticatedOrAdmin]
    queryset = SafersSettings.objects.all()
    serializer_class = SafersSettingsSerializer

    @swagger_fake(None)
    def get_object(self):
        return SafersSettings.load()

###############
# config view #
###############


# class ClientConfigView(APIView):

#     # yapf: disable

#     # ClientConfigView has no serializer to generate a swagger schema from
#     # so I define one here just to make the generated documentation work
#     _config_schema = openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties=OrderedDict((
#             ("foo", openapi.Schema(type=openapi.TYPE_STRING, example="bar")),
#         ))
#     )

#     @swagger_auto_schema(responses={status.HTTP_200_OK: _config_schema})
#     def get(self, request, format=None):
#         """
#         Returns some configuration information required by a client
#         """

#         config = {
#             "foo": "bar",
#         }

#         return Response(config)

