from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property

from rest_framework import generics
# from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from safers.core.decorators import swagger_fake

from safers.users.models import User
from safers.users.permissions import IsSelfOrAdmin
from safers.users.serializers import UserSerializerLite, UserSerializer


class UserView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    lookup_url_kwarg = "user_id"
    # parser_classes = [
    #     MultiPartParser, FormParser
    # ]  # the client sends data as multipart/form data
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @swagger_fake(None)
    def get_object(self):
        if self.kwargs[self.lookup_url_kwarg].upper() == "CURRENT":
            return self.request.user
        return super().get_object()

    @swagger_fake({})
    def get_serializer_context(self):
        # if this is a remote user, I want to prevent updating any
        # profile fields which come from the remote auth_user
        context = super().get_serializer_context()
        user = self.get_object()
        if user.is_remote:
            context["prevent_remote_profile_fields"] = {
                field: getattr(user.profile, field)
                for field in user.auth_user.profile_fields
            }
        return context


class UserViewMixin(object):

    # TODO: NO LONGER USED
    # TODO: CAN PROBABLY DELETE

    # DRY way of accessing user obj for views which rely
    # DRY way of customizing object retrieval for the 2 views below

    @cached_property
    def user(self):
        user_id = self.kwargs["user_id"]
        user = get_object_or_404(User, id=user_id)
        return user

    # @swagger_fake(None)
    # def get_object(self):
    #     qs = self.get_queryset()
    #     qs = self.filter_queryset(qs)
    #     user_uuid = self.kwargs["user_id"]

    #     obj = get_object_or_404(qs, user__uuid=user_uuid)
    #     self.check_object_permissions(self.request, obj)
    #     return obj

    # @swagger_fake(User.objects.none())
    # def get_queryset(self):
    #     return self.customer.customer_users.select_related("user").all()

    def get_serializer_context(self):
        # user might not always be provided to the serializer; therefore,
        # I explicitly update the context to be accessed by ContextVariableDefault as needed
        context = super().get_serializer_context()
        if "user" not in context:
            if getattr(self, "swagger_fake_view", False):
                context["user"] = None
            else:
                context["user"] = self.user
        return context
