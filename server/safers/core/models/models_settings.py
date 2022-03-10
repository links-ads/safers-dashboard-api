from django.db import models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import SingletonMixin


class SafersSettings(SingletonMixin, models.Model):
    class Meta:
        verbose_name = "Safers Settings"
        verbose_name_plural = "Safers Settings"

    allow_registration = models.BooleanField(
        default=True,
        help_text=_("Allow users to register w/ Safers."),
    )

    require_verification = models.BooleanField(
        default=True,
        help_text=_(
            "Require an email verification step to the sign up process."
        ),
    )

    require_terms_acceptance = models.BooleanField(
        default=True,
        help_text=_(
            "Require a user to accept the terms & conditions during the sign up process."
        ),
    )

    max_favorite_alerts = models.PositiveBigIntegerField(
        default=3,
        help_text=_("Number of alerts that a user can mark as 'favorite'."),
    )

    max_favorite_events = models.PositiveBigIntegerField(
        default=3,
        help_text=_("Number of alerts that a user can mark as 'favorite'."),
    )

    def __str__(self):
        return "Safers Settings"
