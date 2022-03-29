import requests

from django.conf import settings

from rest_framework import generics
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters import rest_framework as filters

from safers.core.decorators import swagger_fake
from safers.core.filters import BBoxFilterSetMixin, CharInFilter

from safers.users.authentication import ProxyAuthentication
from safers.users.permissions import IsRemote

from safers.social.models import SocialEvent
from safers.social.serializers import SocialEventSerializer

###########
# filters #
###########


class SocialEventFilterSet(BBoxFilterSetMixin, filters.FilterSet):
    class Meta:
        model = SocialEvent
        fields = {}

    category = CharInFilter(field_name="category", distinct=True)
    severity = CharInFilter(field_name="severity", distinct=True)

    geometry__bboverlaps = filters.Filter(method="filter_geometry")
    geometry__bbcontains = filters.Filter(method="filter_geometry")


##########
# mixins #
##########


class SocialEventMixin():

    filter_backends = (filters.DjangoFilterBackend, )
    filterset_class = SocialEventFilterSet

    lookup_field = "external_id"
    lookup_url_kwarg = "external_id"

    @swagger_fake(SocialEvent.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE EVENTS _THIS_ USER CAN ACCESS
        return SocialEvent.objects.all()


#########
# views #
#########


class SocialEventViewSet(
    SocialEventMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for SocialEvents
    """
    # permission_classes = [TODO: SOME KIND OF FACTORY FUNCTION HERE]
    serializer_class = SocialEventSerializer


class SocialEventDetailListView(SocialEventMixin, generics.ListAPIView):
    """
    ListView for the actual posts referenced by SocialEvents
    """
    permission_classes = SocialEventViewSet.permission_classes + [IsRemote]
    serializer_class = SocialEventSerializer

    def list(self, request, *args, **kwargs):
        data = []

        queryset = self.filter_queryset(self.get_queryset())

        for external_id in queryset.values_list("external_id", flat=True):
            response = requests.get(
                f"{settings.SAFERS_SOCIAL_API_URL}/api/services/app/Social/GetEventByID",
                auth=ProxyAuthentication(request.user),
                params={"Id": external_id},
            )
            response.raise_for_status()
            data.append(response.json())

        return Response(data)


class SocialEventDetailRetrieveView(SocialEventMixin, generics.RetrieveAPIView):
    """
    RetrieveView for the actual posts referenced by SocialEvents
    """
    permission_classes = SocialEventViewSet.permission_classes + [IsRemote]
    serializer_class = SocialEventSerializer

    def retrieve(self, request, *args, **kwargs):

        obj = self.get_object()

        response = requests.get(
            f"{settings.SAFERS_SOCIAL_API_URL}/api/services/app/Social/GetEventByID",
            auth=ProxyAuthentication(request.user),
            params={"Id": obj.external_id},
        )
        response.raise_for_status()

        return Response(response.json())
