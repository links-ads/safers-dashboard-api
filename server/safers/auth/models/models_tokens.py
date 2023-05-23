from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AccessToken(models.Model):
    class Meta:
        ordering = ("created", )
        verbose_name = _("Access Token")
        verbose_name_plural = _("Access Tokens")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    token = models.TextField(_("Access Token"))
    expires_in = models.IntegerField(_("Expires In"), blank=True, null=True)
    token_type = models.CharField(
        _("Token Type"), max_length=64, default="Bearer"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_tokens",
    )

    @property
    def expired(self) -> bool:
        expiry_time = self.created + timedelta(seconds=self.expires_in)
        return timezone.now() <= expiry_time


class RefreshToken(models.Model):
    class Meta:
        ordering = ("created", )
        verbose_name = _("Refresh Token")
        verbose_name_plural = _("Refresh Tokens")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    token = models.TextField(_("Refresh Token"))

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )