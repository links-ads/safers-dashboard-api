from importlib import import_module

from django.conf import settings

from dj_rest_auth.utils import default_create_token


def import_callable(path_or_callable):
    if hasattr(path_or_callable, '__call__'):
        return path_or_callable
    else:
        assert isinstance(path_or_callable, str)
        package, attr = path_or_callable.rsplit('.', 1)
        return getattr(import_module(package), attr)


create_token = import_callable(
    settings.REST_AUTH.get("TOKEN_CREATOR", default_create_token)
)
