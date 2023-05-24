from django.contrib.auth import get_user_model

from rest_framework.authentication import (
    HTTP_HEADER_ENCODING,
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import AuthenticationFailed

from safers.auth.clients import AUTH_CLIENT
from safers.auth.utils import reshape_auth_errors

UserModel = get_user_model()


class OAuth2Authentication(BaseAuthentication):
    """
    Class for performing DRF Authentication using OAuth2 via FusionAuth
    """
    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, token) or None
        if there was no authentication attempt.
        """
        access_token = self.get_access_token(request)
        if not access_token:
            return None

        auth_jwt_response = AUTH_CLIENT.validate_jwt(access_token)
        if not auth_jwt_response.was_successful():
            errors = reshape_auth_errors(auth_jwt_response.error_response)
            raise AuthenticationFailed(errors)
        auth_jwt = auth_jwt_response.success_response["jwt"]
        auth_id = auth_jwt["sub"]

        # TODO: THE JWT HAS THE ID IN IT ALREADY,
        # TODO: SO I GUESS THERE'S NO NEED TO ACTUALLY GET THE USER INFO ?
        # auth_user_response = AUTH_CLIENT.retrieve_user_info_from_access_token(
        #     access_token
        # )
        # if not auth_user_response.was_successful():
        #     errors = reshape_auth_errors(auth_user_response.error_response)
        #     raise AuthenticationFailed(errors)
        # auth_id = auth_user_response.success_response["sub"]

        try:
            user = UserModel.objects.active().get(auth_id=auth_id)
        except UserModel.DoesNotExist as e:
            msg = "User does not exist"
            raise AuthenticationFailed(msg) from e

        return user, access_token

    def get_access_token(self, request):
        """
        Get the access token based on a request.

        Returns None if no authentication details were provided. Raises
        AuthenticationFailed if the token is incorrect.
        """
        header = get_authorization_header(request)
        if not header:
            return None
        header = header.decode(HTTP_HEADER_ENCODING)

        auth = header.split()

        if auth[0].lower() != "bearer":
            return None

        if len(auth) == 1:
            msg = "Invalid 'bearer' header: No credentials provided."
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = "Invalid 'bearer' header: Credentials string should not contain spaces."
            raise AuthenticationFailed(msg)

        return auth[1]