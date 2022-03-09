import email
from email.headerregistry import HeaderRegistry
import requests
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.urls import resolve, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from fusionauth.fusionauth_client import FusionAuthClient

from safers.users.models import User
from safers.users.serializers import LoginSerializer, RegisterSerializer, AuthenticateSerializer
from safers.users.utils import AUTH_CLIENT


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


@method_decorator(
    sensitive_post_parameters("password1"),
    name="dispatch",
)
class LoginView(GenericAPIView):


    _schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=OrderedDict((
            ("email", openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, example="admin@astrosat.net")),
            ("password", openapi.Schema(type=openapi.TYPE_STRING, example="password")),
        )),
    )  # yapf: disable

    serializer_class = LoginSerializer

    @swagger_auto_schema(
        request_body=_schema,
        # responses={status.HTTP_200_OK: TokenSerializer},
    )
    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        import pdb
        pdb.set_trace()

        auth_client = FusionAuthClient(
            settings.FUSION_AUTH_API_KEY,
            settings.FUSION_AUTH_INTERNAL_BASE_URL
        )
        response = auth_client.login(serializer.validated_data)

        redirect_url = request.build_absolute_uri("dashboard")
        # auth_url = f"{settings.FUSION_AUTH_EXTERNAL_BASE_URL}/oauth2/authorize?client_id={settings.FUSION_AUTH_CLIENT_ID}&redirect_uri={redirect_url}&response_type=code"
        auth_url = f"{settings.FUSION_AUTH_INTERNAL_BASE_URL}/oauth2/authorize"
        # response = requests.get(auth_url)
        response = requests.post(
            auth_url,
            data={
                "client_id": settings.FUSION_AUTH_CLIENT_ID,
                "response_type": "code",
                "redirect_uri": redirect_url,
                "loginId": serializer.validated_data["email"],
                "password": serializer.validated_data["password"]
            }
        )
        import pdb
        pdb.set_trace()

        # login to fusionauth
        auth_client = FusionAuthClient(
            settings.FUSION_AUTH_API_KEY,
            settings.FUSION_AUTH_INTERNAL_BASE_URL
        )

        return Response({"hello": "world"})


# I AM HERE
# I OUGHT TO REWRITE AN "AuthorizeView"
# WHICH PERFORMS THE WHOLE REDIRECT CYCLE


class AuthenticateView(GenericAPIView):
    """
    Used as the "redirect_uri" for FusionAuth; Retrieves an auth_code from FusionAuth & 
    exchanges that for an access_token; Uses that access_token to retrieve the auth_user;
    Checks the auth_user against the local db (creates a local user as needed); Then creates
    a local (JWT) token for the client to authenticate future requests against.
    """

    _response_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties=OrderedDict((
            ("token", openapi.Schema(type=openapi.TYPE_STRING)),
        )),
    )  # yapf: disable

    serializer_class = AuthenticateSerializer

    @swagger_auto_schema(
        query_serializer=AuthenticateSerializer,
        responses={status.HTTP_200_OK: _response_schema},
    )
    def get(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        try:
            response = AUTH_CLIENT.exchange_o_auth_code_for_access_token(
                serializer.validated_data["code"],
                settings.FUSION_AUTH_CLIENT_ID,
                # request.build_absolute_uri(request.path),
                request.build_absolute_uri(reverse("authenticate")),
                settings.FUSION_AUTH_CLIENT_SECRET,
            )
            if response.was_successful():
                auth_token = response.success_response["access_token"]
                auth_token_type = response.success_response["token_type"]
                auth_expiry = response.success_response["expires_in"]
                auth_user_id = response.success_response["userId"]

                user, created = User.objects.get_or_create(auth_id=auth_user_id)
                auth_user_data = user.auth_user_data
                if created:
                    # save access_token, etc.
                    pass

                jwt_token = RefreshToken.for_user(user)
                return Response({"token": str(jwt_token.access_token)})
                pass
            else:
                raise Exception(response.error_response)

        except Exception as e:
            raise (e)


##############################
# test views for development #
##############################

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator

from functools import wraps


def fa_authenticated(view_name, view_args=[], view_kwargs={}):
    def _decorator(view_fn):

        fa_client = FusionAuthClient(
            settings.FUSION_AUTH_API_KEY,
            settings.FUSION_AUTH_INTERNAL_BASE_URL,
        )

        @wraps(view_fn)
        def _wrapper(request, *args, **kwargs):

            code = request.GET.get("code")
            if not code:
                redirect_url = request.build_absolute_uri()
                login_url = f"{settings.FUSION_AUTH_EXTERNAL_BASE_URL}/oauth2/authorize?client_id={settings.FUSION_AUTH_CLIENT_ID}&redirect_uri={redirect_url}&response_type=code"
                return redirect(login_url)

            try:
                redirect_url = request.build_absolute_uri(
                    reverse(
                        viewname=view_name, args=view_args, kwargs=view_kwargs
                    )
                )
                response = fa_client.exchange_o_auth_code_for_access_token(
                    code,
                    settings.FUSION_AUTH_CLIENT_ID,
                    redirect_url,
                    settings.FUSION_AUTH_CLIENT_SECRET,
                )
                if response.was_successful():

                    return view_fn(request, *args, **kwargs)

                else:
                    raise Exception(response.error_response)

            except Exception as e:
                raise (e)

        return _wrapper

    return _decorator


# @method_decorator(fa_authenticated("dashboard"), name="dispatch")
class DashboardView(View):
    """
    local page that requires FusionAuth authentication
    shows some private user details
    just for testing/development
    """
    def get(self, request):

        auth_client = FusionAuthClient(
            settings.FUSION_AUTH_API_KEY,
            settings.FUSION_AUTH_INTERNAL_BASE_URL
        )
        code = request.GET.get("code")
        if not code:
            redirect_url = request.build_absolute_uri()
            login_url = f"{settings.FUSION_AUTH_EXTERNAL_BASE_URL}/oauth2/authorize?client_id={settings.FUSION_AUTH_CLIENT_ID}&redirect_uri={redirect_url}&response_type=code"
            return redirect(login_url)

        try:
            redirect_url = request.build_absolute_uri(reverse("dashboard"))
            response = auth_client.exchange_o_auth_code_for_access_token(
                code,
                settings.FUSION_AUTH_CLIENT_ID,
                redirect_url,
                settings.FUSION_AUTH_CLIENT_SECRET,
            )
            if response.was_successful():
                # import pdb
                # pdb.set_trace()
                access_token = response.success_response["access_token"]
                user_id = response.success_response["userId"]
                auth_user = auth_client.retrieve_user(user_id
                                                     ).success_response["user"]
                local_user, _ = User.objects.get_or_create(auth_id=user_id)  # TODO: get email/username as well
                # user_profile = whatever

                SUCCESS_RESPONSE_KEYS = [
                    'access_token', 'expires_in', 'token_type', 'userId'
                ]

                assert str(local_user.auth_id) == auth_user.get("id"), "you got the wrong user"

            else:
                raise Exception(response.error_response)

        except Exception as e:
            raise (e)

        context = {"user": local_user}
        return render(
            request,
            'users/dashboard.html',
            context=context,
        )


def authorized(view_name, view_args=[], view_kwargs={}):
    def _decorator(view_fn):
        @wraps(view_fn)
        def _wrapper(request, *args, **kwargs):

            import pdb
            pdb.set_trace()
            if not request.user.is_authenticated:
                auth_login_url = "{base_url}/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code".format(
                    base_url=settings.FUSION_AUTH_EXTERNAL_BASE_URL,
                    client_id=settings.FUSION_AUTH_CLIENT_ID,
                    redirect_uri=request.build_absolute_uri(
                        reverse("authenticate")
                    ),
                )
                return redirect(auth_login_url)
            else:
                return view_fn(request, *args, **kwargs)

        return _wrapper

    return _decorator

    #         code = request.GET.get("code")
    #         if not code:
    #             redirect_url = request.build_absolute_uri()
    #             login_url = f"{settings.FUSION_AUTH_EXTERNAL_BASE_URL}/oauth2/authorize?client_id={settings.FUSION_AUTH_CLIENT_ID}&redirect_uri={redirect_url}&response_type=code"
    #             return redirect(login_url)

    #         try:
    #             redirect_url = request.build_absolute_uri(
    #                 reverse(
    #                     viewname=view_name, args=view_args, kwargs=view_kwargs
    #                 )
    #             )
    #             response = fa_client.exchange_o_auth_code_for_access_token(
    #                 code,
    #                 settings.FUSION_AUTH_CLIENT_ID,
    #                 redirect_url,
    #                 settings.FUSION_AUTH_CLIENT_SECRET,
    #             )
    #             if response.was_successful():

    #                 return view_fn(request, *args, **kwargs)

    #             else:
    #                 raise Exception(response.error_response)

    #         except Exception as e:
    #             raise (e)

    #     return _wrapper

    # return _decorator


@method_decorator(
    authorized("barfoo"),
    name="dispatch",
)
class xDashboardView(View):
    """
    local page that requires FusionAuth authentication
    shows some private user details
    just for testing/development
    """
    def get(self, request):

        context = {"user": None}
        return render(
            request,
            'users/dashboard.html',
            context=context,
        )
