from rest_framework import serializers

from knox.models import AuthToken as KnoxToken
from knox.settings import knox_settings

from drf_yasg.utils import swagger_serializer_method


class KnoxTokenSerializer(serializers.Serializer):
    # actually serializers a @dataclass instead of a token instance
    access_token = serializers.SerializerMethodField()
    expiry = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def _token_instance(self, obj):
        if isinstance(obj, dict):
            obj = obj["token"]
        return obj.instance

    def _token_key(self, obj):
        if isinstance(obj, dict):
            obj = obj["token"]
        return obj.key

    @swagger_serializer_method(serializers.CharField)
    def get_access_token(self, obj):
        key = self._token_key(obj)
        return key

    @swagger_serializer_method(serializers.DateTimeField)
    def get_expiry(self, obj):
        expiry = self._token_instance(obj).expiry
        return expiry

    # @swagger_serializer_method(knox_settings.USER_SERIALIZER)  # TODO: THIS CAUSES A CIRCULAR IMPORT
    def get_user(self, obj):
        user = self._token_instance(obj).user
        serializer = knox_settings.USER_SERIALIZER(user)
        return serializer.data
