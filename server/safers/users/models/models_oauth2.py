from django.conf import settings
from django.db import models
from django.db.models.query_utils import Q

AUTH_USER_FIELDS = {
    # fields from auth_user to duplicate in user
    "email": "email",
    "username": "username",
}

AUTH_PROFILE_FIELDS = {
    # fields from auth_user to duplicate in user_profile
    "firstName": "first_name",
    "lastName": "last_name",
    "company": "company",
    "address": "address",
    "city": "city",
    "country": "country",  # "avatar": "avatar",
}

AUTH_TOKEN_FIELDS = {
    # fields from auth_token to store in user_data
    "access_token": "access_token",
    "expires_in": "expires_in",
    "refresh_token": "refresh_token",
    "token_type": "token_type",
}


class Oauth2User(models.Model):
    class Meta:
        constraints = [
            # constraints can't span db tables as per:
            # https://forum.djangoproject.com/t/checkconstraint-involving-related-model/5351
            # models.CheckConstraint(
            #     check=(Q(user__is_remote=True)),
            #     name="remote_users_only",
            # )
        ]
        verbose_name = "OAuth2 User Data"
        verbose_name_plural = "OAuth2 User Data"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="auth_user"
    )
    # user = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     related_name="auth_users",
    #     on_delete=models.CASCADE
    # )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_in = models.IntegerField(blank=True, null=True)
    token_type = models.CharField(max_length=64, default="Bearer")

    data = models.JSONField(default=dict)

    @property
    def profile_fields(self):
        """
        Returns the attributes in retreived from oauth2 that are also in AUTH_PROFILE_FIELDS and
        should therefore not be updated by DRF. (This is used by `UserView.get_serializer_context` 
        &  `UserProfileField.validate`.
        """
        # TODO: THIS FEELS LIKE BRITTLE LOGIC; MAY JUST WANT TO HARD-CODE THIS
        return [
            AUTH_PROFILE_FIELDS[k]
            for k in self.data.keys() if k in AUTH_PROFILE_FIELDS
        ]

    def __str__(self):
        return str(self.user)