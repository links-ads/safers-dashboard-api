from django.contrib.auth import get_user_model

from rest_framework import serializers

from safers.auth.models import AccessToken, RefreshToken

UserModel = get_user_model()


class AccessTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = (
            "access_token",
            "expires_in",
            "token_type",
            "user_id",
        )

    access_token = serializers.CharField(source="token")
    user_id = serializers.SlugRelatedField(
        source="user",
        slug_field="id",
        write_only=True,
        queryset=UserModel.objects.all(),
    )


class RefreshTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefreshToken
        fields = (
            "refresh_token",
            "user_id",
        )

    refresh_token = serializers.CharField(source="token")
    user_id = serializers.SlugRelatedField(
        source="user",
        slug_field="id",
        write_only=True,
        queryset=UserModel.objects.all(),
    )


class TokenSerializer(serializers.Serializer):
    """
    Takes data from FusionAuth and creates local tokens using the above
    serializers.
    """

    access_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    token_type = serializers.CharField()
    refresh_token = serializers.CharField()
    user_id = serializers.UUIDField()

    def create(self, validated_data):
        access_token_serializer = AccessTokenSerializer(data=validated_data)
        access_token_serializer.is_valid(raise_exception=True)
        access_token = access_token_serializer.save()
        refresh_token_serializer = RefreshTokenSerializer(data=validated_data)
        refresh_token_serializer.is_valid(raise_exception=True)
        refresh_token = refresh_token_serializer.save()
        return access_token, refresh_token