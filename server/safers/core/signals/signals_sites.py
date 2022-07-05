from django.contrib.sites.models import Site
from django.db.models.signals import post_save

from safers.core.models import SiteProfile


def post_save_site_handler(sender, *args, **kwargs):
    """
    If a Site has just been created,
    then the corresponding Profile must also be created,
    """
    created = kwargs.get("created", False)
    instance = kwargs.get("instance", None)
    if created and instance:
        SiteProfile.objects.create(site=instance)


post_save.connect(
    post_save_site_handler,
    sender=Site,
    dispatch_uid="safers_post_save_site_handler",
)

# no signal handlers are needed for Site post_delete because
# SiteProfile has `on_delete=models.CASCADE`
