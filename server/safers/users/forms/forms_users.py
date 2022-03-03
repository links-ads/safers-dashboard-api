from django.contrib.auth.forms import (
    UserCreationForm as DjangoUserCreationForm, 
    UserChangeForm as DjangoUserChangeForm,
)

from safers.users.models import User


class UserCreationForm(DjangoUserCreationForm):

    class Meta:
        model = User
        fields = ("email",)

class UserChangeForm(DjangoUserChangeForm):

    class Meta:
        model = User
        fields = ("email",)