from django.core.management.base import BaseCommand, CommandError

from safers.auth.clients import AUTH_CLIENT


class Command(BaseCommand):
    """
    Deletes the specified users from FusionAuth
    """

    help = f"Deletes the specified users from FusionAuth."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            dest="emails",
            nargs="+",
            required=True,
            help="email addresses of users to delete",
        )

    def handle(self, *args, **options):
        for email in options["emails"]:
            auth_retrieve_user_response = AUTH_CLIENT.retrieve_user_by_email(
                email
            )
            if auth_retrieve_user_response.was_successful():
                auth_id = auth_retrieve_user_response.success_response["user"][
                    "id"]
                auth_delete_user_reponse = AUTH_CLIENT.delete_user(
                    user_id=auth_id
                )
                if auth_delete_user_reponse.was_successful():
                    self.stdout.write(
                        self.style.SUCCESS(f"deleted remote user '{email}'.")
                    )
                else:
                    self.stdout.write(
                        self.style.
                        ERROR(f"failed to delete remote user: '{email}'.")
                    )

            else:
                self.stdout.write(
                    self.style.
                    WARNING(f"Unable to find remote user: '{email}'.")
                )
