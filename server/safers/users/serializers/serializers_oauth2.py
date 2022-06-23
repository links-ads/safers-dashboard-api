from rest_framework import serializers


class AuthenticateSerializer(serializers.Serializer):
    """
    serializer used to authenticate code
    """
    code = serializers.CharField(required=False)
    locale = serializers.CharField(required=False)
    userState = serializers.CharField(required=False)
    error = serializers.CharField(required=False)

    def validate(self, data):
        validated_data = super().validate(data)
        if validated_data.get("error") or not validated_data.get("code"):
            raise serializers.ValidationError("bad code")
        return validated_data
