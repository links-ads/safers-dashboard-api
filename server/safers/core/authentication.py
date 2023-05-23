from requests.auth import AuthBase


class TokenAuthentication(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers["Authorization"] = self.token
        return request


class BearerAuthentication(TokenAuthentication):
    def __call__(self, request):
        request.headers["Authorization"] = "Bearer " + self.token
        return request