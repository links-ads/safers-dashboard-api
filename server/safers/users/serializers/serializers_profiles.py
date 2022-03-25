from rest_framework import serializers

from safers.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            "first_name",
            "last_name",
            "company",
            "address",
            "city",
            "country",
            "avatar",
            "remote_profile_fields",
        )

    remote_profile_fields = serializers.SerializerMethodField()

    def get_remote_profile_fields(self, obj):
        """
        used to indicate to the frontend which profile fields should be read-only
        """
        return self.context.get("prevent_remote_profile_fields", {}).keys()

    def validate(self, data):
        # TODO: CAN REFACTOR THIS NOW THAT Oauth2User HAS A profile_fields PROPERTY
        remote_profile_field_errors = {
            k: ["Unable to update remote profile fields."]
            for k, v in self.context.get("prevent_remote_profile_fields", {}).items()
            if k in data and data[k] != v
        }  # yapf: disable


        if remote_profile_field_errors:
            raise serializers.ValidationError(remote_profile_field_errors)
        return data