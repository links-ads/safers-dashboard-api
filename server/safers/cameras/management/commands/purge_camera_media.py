from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from safers.cameras.models import CameraMedia


class Command(BaseCommand):
    """
    Deletes all (non-smoke/fire) camera_media instances from the db that fall 
    outside `SafersSettings.camera_media_preserve_timerange`
    """

    help = f"Deletes all (non-smoke/fire) camera_media instances that are older than {settings.SAFERS_CAMERA_MEDIA_PRESERVE_TIMERANGE}."

    def add_arguments(self, parser):

        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help=
            "Don't actually delete anything, just report what _would_ be deleted."
        )

    def handle(self, *args, **options):

        dry_run = options["dry_run"]

        try:
            preserve_timestamp = timezone.now(
            ) - settings.SAFERS_CAMERA_MEDIA_PRESERVE_TIMERANGE
            camera_media_to_delete = CameraMedia.objects.undetected().filter(
                timestamp__lte=preserve_timestamp
            )

            if dry_run:
                msg = f"{camera_media_to_delete.count()} CameraMedia objects ready to delete."
                self.stdout.write(msg)

            else:
                # (cannot do bulk deletion b/c `undetected` filter uses `distinct` so using loop below)
                with transaction.atomic():
                    for camera_media in camera_media_to_delete:
                        camera_media.delete()
                    msg = f"Deleted {camera_media_to_delete.count()} CameraMedia objects."
                    self.stdout.write(msg)

        except Exception as e:
            raise CommandError(e)
