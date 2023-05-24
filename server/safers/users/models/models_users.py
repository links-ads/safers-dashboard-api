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

from model_utils import FieldTracker

from safers.core.authentication import TokenAuthentication
from safers.core.clients import GATEWAY_CLIENT

from safers.users.models import Organization, Role

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


class UserStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    COMPLETED = "COMPLETED", _("Completed")


########################
# managers & querysets #
########################


class UserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        if not email:
            raise ValueError('The given email must be set')

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
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)

    def local(self):
        return self.filter(_is_local=True)

    def remote(self):
        return self.filter(_is_remote=True)


##########
# models #
##########


class User(AbstractUser):
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    objects = UserManager.from_queryset(UserQuerySet)()

    tracker = FieldTracker()

    # remove these fields, as they should form part of the profile
    first_name = None
    last_name = None

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    email = models.EmailField(
        _('email address'),
        blank=False,
        unique=True,
    )

    auth_id = models.UUIDField(
        blank=True,
        editable=False,
        null=True,
        unique=True,
        help_text=_("The corresponding id of the FusionAuth User"),
    )

    change_password = models.BooleanField(
        default=False,
        help_text=_("Force user to change password at next login."),
    )

    accepted_terms = models.BooleanField(
        default=False,
        help_text=_("Has this user accepted the terms & conditions?"),
    )

    status = models.CharField(
        max_length=64,
        choices=UserStatus.choices,
        default=UserStatus.PENDING,
        help_text=_("What stage of registration is this user at?"),
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
    def is_citizen(self) -> bool:
        role = self.role
        return role and role.is_citizen

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
        """
        synchronize UserProfile information bewteen the dashboard and gateway
        """
        if direction == ProfileDirection.REMOTE_TO_LOCAL:
            remote_profile_data = GATEWAY_CLIENT.get_profile(
                auth=TokenAuthentication(token)
            )
            self.profile = {
                k: v
                for k,
                v in remote_profile_data["profile"].items()
                if k in PROFILE_FIELDS
            }
            # don't forget to update role & organization...
            role = next(
                iter(remote_profile_data["profile"]["user"].get("roles", [])),
                None
            )
            if role is not None:
                self.role_name = role
            organization = remote_profile_data["profile"].get("organization")
            if organization is not None:
                self.organization_name = organization.get("name")

        elif direction == ProfileDirection.LOCAL_TO_REMOTE:
            local_profile_data = dict(
                organizationId=self.organization.id
                if self.organization else None,
                **(self.profile)
            )
            GATEWAY_CLIENT.update_profile(
                auth=TokenAuthentication(token), data=local_profile_data
            )

        else:
            raise ValueError(f"Unknown direction: '{direction}'.")

    def save(self, *args, **kwargs):
        if self.tracker.has_changed("status"):
            # TODO: DO SOMETHING WITH SIGNALS HERE ?
            old_status = self.tracker.previous("status")
            new_status = self.status
        return super().save(*args, **kwargs)