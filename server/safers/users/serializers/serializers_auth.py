from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

class RegisterSerializer(serializers.Serializer):
    # username = serializers.CharField()
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_email(self, email):
        return email

    def validate_password1(self, password):
        django_validate_password(password) 
        return password        

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(_("The two password fields didn't match."))
        return data