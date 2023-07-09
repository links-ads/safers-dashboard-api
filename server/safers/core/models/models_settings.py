from datetime import timedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from safers.core.mixins import SingletonMixin


class SafersSettings(SingletonMixin, models.Model):
    class Meta:
        verbose_name = "Safers Settings"
        verbose_name_plural = "Safers Settings"

    display_dashboard_notifications = models.BooleanField(
        default=True,
        help_text=_("Display the top panel of the general dashboard."),
    )

    display_menu_notifications = models.BooleanField(
        default=True,
        help_text=_("Display the notification icons on the sidebar menu."),
    )

    profile = models.BooleanField(
        default=False,
        help_text=_("Enable silk profiling on API Views."),
    )

    allow_signup = models.BooleanField(
        default=True,
        help_text=_("Allow users to register w/ the dashboard."),
    )

    allow_signin = models.BooleanField(
        default=True,
        help_text=_("Allow users to signin w/ the dashboard."),
    )

    allow_password_change = models.BooleanField(
        default=False,
        help_text=_("Allow users to change their password via the dashboard.")
    )

    require_terms_acceptance = models.BooleanField(
        default=True,
        help_text=_(
            "Require a user to accept the terms & conditions during the sign up process."
        ),
    )

    allow_remote_deletion = models.BooleanField(
        default=False,
        help_text=_(
            "When deleting a user from the dashboard also delete a user from all of safers."
        ),
    )

    polling_frequency = models.FloatField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text=_(
            "The frequency (in seconds) that the frontend should poll the backend for new data. "
            "Set to 0 to disable polling."
        ),
    )

    request_timeout = models.FloatField(
        default=6000,
        validators=[MinValueValidator(0)],
        help_text=_(
            "The time (in milliseconds) for the frontend to wait for a response from the backend. "
            "Set to 0 to have no timeout."
        )
    )

    max_favorite_alerts = models.PositiveBigIntegerField(
        default=3,
        help_text=_("Number of alerts that a user can mark as 'favorite'."),
    )

    max_favorite_events = models.PositiveBigIntegerField(
        default=3,
        help_text=_("Number of alerts that a user can mark as 'favorite'."),
    )

    max_favorite_camera_media = models.PositiveBigIntegerField(
        default=3,
        help_text=_(
            "Number of camera_medias that a user can mark as 'favorite'."
        ),
    )

    camera_media_preserve_timerange = models.DurationField(
        default=timedelta(hours=24),
        help_text=_(
            "Time range of (non smoke/fire) camera_medias to preserve; everything outside of this range is purged."
        )
    )

    camera_media_trigger_alert_timerange = models.DurationField(
        default=timedelta(hours=1),
        help_text=_(
            "Time range between successive smoke/fire camera_medias that will trigger an alert."
        )
    )

    default_timerange = models.DurationField(
        default=timedelta(days=3),
        help_text=_(
            "Time range to use in date/datetime filters when no explicit filter is provided."
        )
    )

    possible_event_distance = models.FloatField(
        default=10.0,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text=_(
            "Radius (in kms) within which alerts can be transformed into events"
        )
    )

    possible_event_timerange = models.FloatField(
        default=72.0,
        validators=[MinValueValidator(0), MaxValueValidator(168)],
        help_text=_(
            "Time range (in hours) within which alerts can be transformed into events"
        )
    )

    def __str__(self):
        return "Safers Settings"
