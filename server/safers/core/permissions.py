from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedOrAdmin(BasePermission):
    """
    any authenticated user can access a safe method;
    but only the admin can access other methods
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return user.is_authenticated
        else:
            return user.is_superuser
