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

    def __str__(self):
        return "Safers Settings"


