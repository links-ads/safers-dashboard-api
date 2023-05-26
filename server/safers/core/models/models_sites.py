from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _

from colorfield.fields import ColorField


class AdminNoticeColorSamples(models.TextChoices):
    """
    Suggested colors for the site-specific Admin Notice.
    """
    DEVELOPMENT = "#CCCCCC", _("Grey")
    TESTING = "#009933", _("Green")
    STAGING = "#FFAA00", _("Yellow")
    PRODUCTION = "#FF0000", _("Red")


class SiteProfile(models.Model):
    class Meta:
        verbose_name = "Site Profile"
        verbose_name_plural = "Site Profiles"

    site = models.OneToOneField(
        Site,
        on_delete=models.CASCADE,
        related_name="profile",
        help_text=_("Associated site."),
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text=_("Description of site."),
    )

    code = models.CharField(
        max_length=8,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Unique code to identify this site (to RMQ)."),
    )

    show_admin_notice = models.BooleanField(
        default=False,
        help_text=_(
            "Whether or not to show a site-specific notice in the Admin."
        ),
    )

    admin_notice_color = ColorField(
        default=AdminNoticeColorSamples.DEVELOPMENT,
        samples=AdminNoticeColorSamples.choices,
        help_text=_("Color of site-specific notice in the Admin."),
    )

    def __str__(self) -> str:
        return str(self.site)

    def save(self, *args, **kwargs):
        # if a SiteProfile has changed, make sure the next time current_site
        # is accessed it is taken from the db rather than from the cache.
        Site.objects.clear_cache()
        return super().save(*args, **kwargs)