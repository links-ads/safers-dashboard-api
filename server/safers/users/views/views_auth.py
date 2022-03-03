from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import permissions

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

# from django.conf import settings
# from django.contrib.auth.models import User
# from django.shortcuts import render, redirect, reverse
# from django.views.generic import View

from fusionauth.fusionauth_client import FusionAuthClient

from safers.users.serializers import RegisterSerializer

@method_decorator(
  sensitive_post_parameters("password1", "password2"), 
  name="dispatch",
)
class RegisterView(CreateAPIView):

  # permission_classes = []
  serializer_class = RegisterSerializer
  # token_model = TokenModel

  def create(self, request, *args, **kwargs):
      serializer = self.get_serializer(data=request.data)
      serializer.is_valid(raise_exception=True)
      data = {"foo": "bar"}
      response = Response(data, status=status.HTTP_201_CREATED)
      return response
# # class DashboardView(View):

# #   def get(self, request):
# #     if not user_login_ok(request):
# #       login_url = get_login_url(request)
# #       return redirect(login_url)

# #     birthday = None
# #     user = None

# #     try:
# #       client = FusionAuthClient(
# #         settings.FUSION_AUTH_API_KEY, settings.FUSION_AUTH_BASE_URL
# #       )
# #       r = client.retrieve_user(request.user.username)

# #       if r.was_successful():
# #         user = r.success_response
# #         birthday = user["user"]["birthDate"]
# #       else:
# #         print(r.error_response)
# #     except Exception as e:
# #       print("couldn't get user")
# #       print(e)

# #     return render(request, "secretbirthdaysapp/dashboard.html", {"birthday": birthday})