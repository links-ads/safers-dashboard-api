from requests.auth import AuthBase


class ProxyAuthentication(AuthBase):
    def __init__(self, user):
        assert user.is_remote, "trying to authenticate w/out remote credentials"
        self.auth_user = user.auth_user

    def __call__(self, request):
        request.headers["Authorization"] = self.token_string
        return request

    @property
    def token_string(self):
        return self.auth_user.access_token


class ProxyBearerAuthentication(ProxyAuthentication):
    @property
    def token_string(self):
        return "Bearer " + self.auth_user.access_token
