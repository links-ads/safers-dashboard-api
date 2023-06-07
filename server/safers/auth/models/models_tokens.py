from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import ExpressionWrapper, F, Q
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AccessTokenManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        return qs.annotate(
            _expiry_time=ExpressionWrapper(
                F("created") + F("expires_in"),
                output_field=models.DateTimeField()
            )
        )


class AccessTokenQuerySet(models.QuerySet):
    def expired(self):
        return self.filter(_expiry_time__lte=timezone.now())

    def unexpired(self):
        return self.exclude(_expiry_time__lte=timezone.now())


class AccessToken(models.Model):
    class Meta:
        ordering = ("created", )
        verbose_name = _("Access Token")
        verbose_name_plural = _("Access Tokens")

    objects = AccessTokenManager.from_queryset(AccessTokenQuerySet)()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    token = models.TextField(_("Access Token"))

    expires_in = models.DurationField(
        # FusionAuth returns an integer the dashboard converts it to a timedelta
        _("Expires In"),
        blank=True,
        null=True,
    )

    token_type = models.CharField(
        _("Token Type"),
        max_length=64,
        default="Bearer",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="access_tokens",
    )

    @property
    def expired(self) -> bool:
        expiry_time = self.created + self.expires_in
        return timezone.now() >= expiry_time


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