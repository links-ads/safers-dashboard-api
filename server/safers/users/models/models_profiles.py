from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.db import models
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _

###########
# helpers #
###########

MAX_AVATAR_WIDTH, MAX_AVATAR_HEIGHT = (9999, 9999)


def avatar_file_path(instance, filename):
    return f"users/{instance.user.id}/profile/{filename}"


def validate_avatar_dimensions(value):
    width, height = get_image_dimensions(value)
    if width >= MAX_AVATAR_WIDTH or height >= MAX_AVATAR_HEIGHT:
        raise ValidationError(
            f"Image dimensions cannot exceed {MAX_AVATAR_WIDTH}px x {MAX_AVATAR_HEIGHT}px.  (They were {width}px x {height}px.)"
        )


########################
# managers & querysets #
########################


class UserProfileManager(models.Manager):
    pass


class UserProfileQuerySet(models.QuerySet):
    pass


##########
# models #
##########


class UserProfile(models.Model):
    """
    A custom UserProfile for Safers Users.
    Much of the actual UserProfile & Authentication Logic comes from FusionAuth (except when it doesn't).
    """
    class Meta:
        constraints = [
            # constraints can't span db tables as per:
            # https://forum.djangoproject.com/t/checkconstraint-involving-related-model/5351
            # models.CheckConstraint(
            #     check=(Q(user__is_local=True)),
            #     name="local_users_only",
            # )
        ]
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    objects = UserProfileManager.from_queryset(UserProfileQuerySet)()

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    # dashboard-specific fields, like `default_aoi` and `favorite_alerts` are stored on User
    # the profile includes fields that could come from FusionAuth if the user was remote

    first_name = models.CharField(max_length=255, blank=True, null=True)

    last_name = models.CharField(max_length=255, blank=True, null=True)

    company = models.CharField(max_length=255, blank=True, null=True)

    address = models.CharField(max_length=255, blank=True, null=True)

    city = models.CharField(max_length=255, blank=True, null=True)

    country = models.CharField(max_length=255, blank=True, null=True)

    avatar = models.ImageField(
        # TODO: PRIVATE STORAGE (HOW TO SPECIFY THIS IN DEVELOPMENT?)
        upload_to=avatar_file_path,
        validators=[validate_avatar_dimensions],
        blank=True,
        null=True
    )

    def __str__(self):
        return str(self.user)
