from django.conf import settings
from django.db import models
from django.db.models.query_utils import Q


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
        verbose_name = "User Profile (oauth2)"
        verbose_name_plural = "User Profiles (oauth2)"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="auth_users",
        on_delete=models.CASCADE
    )
    data = models.JSONField()

    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)

    def __str__(self):
        return str(self.user)