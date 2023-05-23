from rest_framework.permissions import BasePermission, SAFE_METHODS

from functools import partial

from django.conf import settings


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
