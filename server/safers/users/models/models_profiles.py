import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.expressions import ExpressionWrapper
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _

from fusionauth.fusionauth_client import FusionAuthClient

# AUTH_CLIENT = FusionAuthClient(settings.FUSION_AUTH_API_KEY, settings.FUSION_AUTH_BASE_URL)


########################
# managers & querysets #
########################


class UserProfileManager(models.Manager):
  
    def get_queryset(self):
        """
        Add some calculated fields to the default queryset
        """
        qs = super().get_queryset()
        return qs.annotate(
            # is_local=ExpressionWrapper(
            #     Q(local_user__isnull=False) & Q(auth_id__isnull=True),
            #     output_field=models.BooleanField()
            # ),
            # is_remote=ExpressionWrapper(
            #     Q(local_user__isnull=True) & Q(auth_id__isnull=False),
            #     output_field=models.BooleanField()
            # )
        )


class UserProfileQuerySet(models.QuerySet):

    def local(self):
        return self.filter(is_local=True)

    def remote(self):
        return self.filter(is_remote=True)

##########
# models #
##########

class UserProfile(models.Model):
    """
    A custom user profile for Safers Users.
    The actual User Model & Authentication Logic comes from FusionAuth (except when it doesn't).
    But this class acts as a container for app-specific fields.
    """
    class Meta:
        constraints = [
            # models.CheckConstraint(
            #     check=(
            #         Q(
            #             auth_id__isnull=False, 
            #             local_user__isnull=True,
            #         ) 
            #         | Q(
            #             auth_id__isnull=True, 
            #             local_user__isnull=False,
            #         )
            #     ),
            #     name="local_or_remote"
            # )
        ]
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    objects = UserProfileManager.from_queryset(UserProfileQuerySet)()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    auth_id = models.UUIDField(editable=False, blank=True, null=True, help_text=_("The corresponding id of the FusionAuth User"))
    # local_user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE, help_text=_("A local user to access safers while bypassing FusionAuth (used for admin and testing and development)."))
    
    # is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user)

    # @property
    # def is_local(self):
    #     return self.local_user and not self.auth_id

    # @property
    # def is_remote(self):
    #     return not self.local_user and self.auth_id

    @property
    def user(self):
        return "foobar"
        # return self.local_user or AUTH_CLIENT.retrieve_user(self.auth_id)
        
