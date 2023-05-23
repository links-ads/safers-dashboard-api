from enum import Enum
import uuid

from django.apps import apps
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models
from django.db.models.expressions import ExpressionWrapper
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _

from safers.users.models import Organization, Role
from safers.users.utils import AUTH_CLIENT

###########
# helpers #
###########

PROFILE_FIELDS = [
    # profile fields to retain from gateway
    "user",
    "organizationId",
    "teamId",
    "personId",
    "isFirstLogin",
    "isNewUser",
    "taxCode",
]


class ProfileDirection(str, Enum):
    """
    Indicates whether to synchronize the profile from the dashboard
    (local) to the gateway (remote).
    """
    LOCAL_TO_REMOTE = "local_to_remote"
    REMOTE_TO_LOCAL = "remote_to_local"


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

    def get_queryset(self):
        """
        Add some calculated fields to the default queryset
        """
        qs = super().get_queryset()

        return qs.annotate(
            _is_local=ExpressionWrapper(
                Q(auth_id__isnull=True), output_field=models.BooleanField()
            ),
            _is_remote=ExpressionWrapper(
                Q(auth_id__isnull=False), output_field=models.BooleanField()
            )
        )

    class UserQuerySet(models.QuerySet):
        def local(self):
            return self.filter(_is_local=True)

        def remote(self):
            return self.filter(_is_remote=True)


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

    # remove these fields, as they should form part of the profile
    first_name = None
    last_name = None

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    auth_id = models.UUIDField(
        blank=True,
        editable=False,
        null=True,
        unique=True,
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

    organization_name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )

    role_name = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )

    profile = models.JSONField(
        default=dict,
        help_text=_(
            "JSON representation of profile; used for synchronization w/ gateway."
        ),
    )

    default_aoi = models.ForeignKey(
        "aois.Aoi",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    favorite_alerts = models.ManyToManyField(
        "alerts.Alert", related_name="favorited_users", blank=True
    )

    favorite_events = models.ManyToManyField(
        "events.Event", related_name="favorited_users", blank=True
    )

    favorite_camera_medias = models.ManyToManyField(
        "cameras.CameraMedia", related_name="favorited_users", blank=True
    )

    @property
    def is_local(self):
        return self.auth_id is None

    @property
    def is_remote(self):
        return self.auth_id is not None

    @property
    def is_citizen(self):
        return self.role and self.role.name == "citizen"

    @property
    def is_professional(self):
        return self.role and self.role.name != "citizen"

    @property
    def organization(self) -> Organization | None:
        try:
            return Organization.objects.get(name=self.organization_name)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

    @property
    def role(self) -> Role | None:
        try:
            return Role.objects.get(name=self.role_name)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

    def synchronize_profile(
        self, token: str, direction: ProfileDirection
    ) -> None:
        # TODO: IMPLEMENT THIS ONCE GATEWAY_CLIENT HAS BEEN ADDED
        raise NotImplementedError()