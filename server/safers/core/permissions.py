from rest_framework.permissions import BasePermission, SAFE_METHODS

from functools import partial

from django.conf import settings
from django.contrib.admin import AdminSite

#####################
# admin permissions #
#####################


def has_admin_site_permission(request, group_names=[]):
    """
    Returns a boolean indicating whether or not a user has permission to access an AdminSite.
    Just like the built-in AdminSite.has_permission function, except also checks for memebership
    in an arbitrary list of groups.
    """
    user = request.user
    permission = user.is_active and user.is_staff
    in_groups = [
        user.groups.filter(name=group_name).exists()
        for group_name in group_names
    ]
    return permission and all(in_groups)


default_admin_site_has_permission = partial(
    has_admin_site_permission, group_names=["AdminGroup"]
)

#####################
# other permissions #
#####################


class IsAdminOrAuthenticated(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return user.is_authenticated
        return user.is_superuser


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_superuser


class IsAdminOrDebug(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_superuser or settings.DEBUG
