import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from allauth.account.models import EmailAddress

from safers.users.utils import AUTH_CLIENT

########################
# managers & querysets #
########################


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        if not email:
            raise ValueError('The given email must be set')
        if not username:
            username = email

        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        email = self.normalize_email(email)

        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self, username, email=None, password=None, **extra_fields
    ):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        if not username:
            username = email

        return self.create_user(username, email, password, **extra_fields)


##########
# models #
##########


class User(AbstractUser):
    """
    A custom user w/ a UUID for pk, a required (unique) email address, 
    and a custom manager that uses the email address for username as a default.
    """
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    objects = UserManager()

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    auth_id = models.UUIDField(
        blank=True,
        editable=False,
        null=True,
        # TODO: unique=True
        help_text=_("The corresponding id of the FusionAuth User"),
    )

    email = models.EmailField(_('email address'), unique=True)

    change_password = models.BooleanField(
        default=False,
        help_text=_("Force user to change password at next login.")
    )

    accepted_terms = models.BooleanField(
        default=False,
        help_text=_("Has this user accepted the terms & conditions?")
    )

    role = models.ForeignKey(
        "Role",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    organization = models.ForeignKey(
        "Organization",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    default_aoi = models.ForeignKey(
        "aois.Aoi",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    # favorite alerts
    # favorite events

    def verify(self):
        """
        Manually verifies a user's primary email address
        """

        emailaddresses = self.emailaddress_set.all()

        try:
            primary_emailaddress = emailaddresses.get(primary=True)
        except EmailAddress.DoesNotExist:
            primary_emailaddress, _ = EmailAddress.objects.get_or_create(
                user=self, email=self.email
            )
            primary_emailaddress.set_as_primary(conditional=True)

        primary_emailaddress.verified = True
        primary_emailaddress.save()

    @property
    def is_verified(self):
        """
        Checks if the primary email address belonging to this user has been verified.
        """
        return (
            self.emailaddress_set.only("verified", "primary").filter(
                primary=True, verified=True
            ).exists()
        )

    @property
    def auth_user_data(self):

        try:
            auth_user_response = AUTH_CLIENT.retrieve_user(self.auth_id)
            if auth_user_response.was_successful():
                return auth_user_response.success_response["user"]
            else:
                raise Exception(auth_user_response.error_response)

        except Exception as e:
            raise e  # I AM HERE
