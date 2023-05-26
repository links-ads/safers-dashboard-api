from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

DEFAULT_SITE_DOMAIN = "localhost:8000"


class Command(BaseCommand):
    """
    Updates the Sites table.
    """

    help = "Updates a Site object w/ a specific domain."

    def add_arguments(self, parser):

        parser.add_argument(
            "--id",
            dest="id",
            default=settings.SITE_ID,
            required=False,
            help=_(
                "ID of Site to update (if unprovied will use the default SITE_ID specified in settings)."
            ),
        )

        parser.add_argument(
            "--domain",
            dest="domain",
            required=False,
            default=DEFAULT_SITE_DOMAIN,
            help=
            f"Domain to update the Site with (if unprovided will use '{DEFAULT_SITE_DOMAIN}'",
        )

        parser.add_argument(
            "--name",
            dest="name",
            required=False,
            default=None,
            help=_(
                "Name to update the Site with (if unprovided will just use the domain)."
            ),
        )

    def handle(self, *args, **options):

        try:

            domain = options.get("domain")
            name = options.get("name") or domain

            site, created = Site.objects.update_or_create(
                id=options["id"],
                defaults={
                    "domain": domain[:100], "name": name[:50]
                }
            )

        except IntegrityError:
            raise CommandError(f"The domain '{domain}' is already in use.")

        except Exception as e:
            raise CommandError(str(e))

        if options["verbosity"] >= 1:
            self.stdout.write(
                f"successfully {'created' if created else 'updated'} Site: {site}."
            )