from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.core.cache import caches, InvalidCacheBackendError
from django.utils.translation import gettext_lazy as _


class Command(BaseCommand):
    """
    Clears the cache
    """
    help = "Clears the contents of the cache."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--name",
            dest="name",
            default="default",
            required=False,
            help=_("name of cache to clear"),
        )

    def handle(self, *args, **options):

        try:
            cache = caches[options["name"]]
            cache.clear()
        except InvalidCacheBackendError as e:
            raise CommandError(
                f"Unable to find a cache named '{options['name']}'."
            ) from e

        if options["verbosity"] >= 1:
            self.stdout.write(f"successfully cleared cache: {cache}.")