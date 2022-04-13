from requests.auth import AuthBase


class ProxyAuthentication(AuthBase):
    def __init__(self, user):
        assert user.is_remote, "trying to authentication w/out remote credentials"
        self.auth_user = user.auth_user

    def __call__(self, request):
        request.headers["Authorization"] = self.auth_user.access_token
        # request.headers["Authorization"] \
        #     = "Bearer " + self.auth_user.access_token
        return request
