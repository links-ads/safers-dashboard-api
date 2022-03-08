from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from safers.core.decorators import swagger_fake

from safers.users.models import User
from safers.users.permissions import IsSelfOrAdmin
from safers.users.serializers import UserSerializer


class UserView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    lookup_url_kwarg = "user_id"
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        import pdb
        pdb.set_trace()
        return super().get(request, *args, **kwargs)


class UserViewMixin(object):

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
