from django.contrib.sites.models import Site
from django.db import models


class SiteProfile(models.Model):
    class Meta:
        verbose_name = "Site Profile"
        verbose_name_plural = "Site Profiles"

    site = models.OneToOneField(
        Site, on_delete=models.CASCADE, related_name="profile"
    )

    code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.site)
