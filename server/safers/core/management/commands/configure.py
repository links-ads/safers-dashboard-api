import os

from django.apps import apps
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError


def load_fixture(app_config, fixture_name):
    fixture_path = os.path.join(app_config.path, "fixtures", fixture_name)
    management.call_command("loaddata", fixture_path)


class Command(BaseCommand):
    """
    Sets up initial configuration for safers-dashbaord-api.
    This includes loading fixtures and setting a unique site_code.
    """

    help = f"Setup initial configuration for {settings.PROJECT_NAME}."

    def add_arguments(self, parser):

        parser.add_argument(
            "--site_code",
            dest="site_code",
            help=
            "A unique code associated w/ this site to use when generating routing_keys (to distinguish it from other sites)."
        )

        parser.add_argument(
            "--skip-aois",
            dest="load_aois",
            action="store_false",
            help="Whether or not to skip the AOI fixtures.",
        )

        parser.add_argument(
            "--skip-cameras",
            dest="load_cameras",
            action="store_false",
            help="Whether or not to skip the Camer fixtures.",
        )

        parser.add_argument(
            "--skip-data",
            dest="load_data",
            action="store_false",
            help="Whether or not to skip the DataType fixtures.",
        )

        parser.add_argument(
            "--skip-organizations",
            dest="load_organizations",
            action="store_false",
            help="Whether or not to skip the users.Organization fixtures.",
        )

        parser.add_argument(
            "--skip-roles",
            dest="load_roles",
            action="store_false",
            help="Whether or not to skip the users.Role fixtures.",
        )

    def handle(self, *args, **options):

        try:

            site_code = options["site_code"]
            if site_code:
                current_site_profile = get_current_site(None).profile
                current_site_profile.code = site_code
                current_site_profile.save()
                self.stdout.write("updated site_profile code")

            if options["load_aois"]:
                load_fixture(
                    apps.get_app_config("aois"),
                    "aois_fixture.json",
                )

            if options["load_cameras"]:
                load_fixture(
                    apps.get_app_config("cameras"),
                    "cameras_fixture.json",
                )

            if options["load_data"]:
                load_fixture(
                    apps.get_app_config("data"),
                    "datatypes_fixture.json",
                )

            if options["load_organizations"]:
                load_fixture(
                    apps.get_app_config("users"),
                    "organizations_fixture.json",
                )

            if options["load_roles"]:
                load_fixture(
                    apps.get_app_config("users"),
                    "roles_fixture.json",
                )

        except Exception as e:
            raise CommandError(e)
