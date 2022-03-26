import imp
from rest_framework import mixins
from rest_framework import viewsets

from safers.core.decorators import swagger_fake

from safers.social.models import Tweet
from safers.social.serializers import TweetSerializer


class TweetViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    # permission_classes = [TODO: SOME KIND OF FACTORY FUNCTION HERE]
    serializer_class = TweetSerializer
    lookup_field = "tweet_id"
    lookup_url_kwarg = "tweet_id"

    @swagger_fake(Tweet.objects.none())
    def get_queryset(self):
        user = self.request.user
        # TODO: GET ALL THE ALERTS THIS USER CAN ACCESS
        return Tweet.objects.all()
