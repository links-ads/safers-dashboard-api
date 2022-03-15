from django.db import models

from safers.users.models import User


class Oauth2User(models.Model):
    class Meta:
        verbose_name = "User (oauth2)"
        verbose_name_plural = "Users (oauth2)"

    user = models.ForeignKey(
        User, related_name="auth_user", on_delete=models.CASCADE
    )
    data = models.JSONField()

    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)

    def __str__(self):
        return str(self.user)