from django.conf import settings
from django.db import models
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _

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
    The actual UserProfile & Authentication Logic comes from FusionAuth (except when it doesn't).
    This class is here in case a user has logged on locally
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
        verbose_name = "User Profile (local)"
        verbose_name_plural = "User Profiles (local)"

    objects = UserProfileManager.from_queryset(UserProfileQuerySet)()

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    def __str__(self):
        return str(self.user)
