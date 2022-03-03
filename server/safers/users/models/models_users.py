import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from fusionauth.fusionauth_client import FusionAuthClient

AUTH_CLIENT = FusionAuthClient(settings.FUSION_AUTH_API_KEY, settings.FUSION_AUTH_BASE_URL)


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
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)        
        username = GlobalUserModel.normalize_username(username)
        email = self.normalize_email(email)

        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,)
    auth_id = models.UUIDField(editable=False, blank=True, null=True, help_text=_("The corresponding id of the FusionAuth User"),)

    email = models.EmailField(_('email address'), unique=True)

    @property
    def auth_user(self):
        try:
            return AUTH_CLIENT.retrieve_user(self.auth_id)
        except Exception as e:
            raise e  # I AM HERE
