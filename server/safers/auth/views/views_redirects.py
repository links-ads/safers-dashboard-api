from urllib.parse import urljoin, urlencode

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from safers.core.models import SafersSettings


@require_http_methods(["GET"])
def login_view(request):
    """"
    Login via FusionAuth and then redirect to the client callback.
    That callback should make a request to AuthenticateView above.
    """
    AUTHENTICATION_CODE_GRANT_PATH = "oauth2/authorize"
    base_auth_url = urljoin(
        settings.FUSIONAUTH_EXTERNAL_URL, AUTHENTICATION_CODE_GRANT_PATH
    )
    auth_url_params = urlencode({
        "client_id": settings.FUSIONAUTH_CLIENT_ID,
        "redirect_uri": settings.FUSIONAUTH_REDIRECT_URL,
        "tenant_id": settings.FUSIONAUTH_TENANT_ID,
        "response_type": "code",
        "scope": "offline_access",
    })
    auth_url = f"{base_auth_url}?{auth_url_params}"

    return HttpResponseRedirect(auth_url)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """"
    Logout in Django then logout via FusionAuth and then redirect to
    the client callback.
    """
    safers_settings = SafersSettings.load()
    if request.method == "GET" and not safers_settings.allow_logout_via_get:
        return HttpResponseNotAllowed(["POST"])

    user = request.user
    # TODO: NEED TO BE A BIT MORE JUDICIOUS W/ WHAT GETS DELETED
    user.access_tokens.all().delete()
    user.refresh_tokens.all().delete()
    logout(request)

    LOGOUT_PATH = "oauth2/logout"
    base_auth_url = urljoin(settings.FUSIONAUTH_EXTERNAL_URL, LOGOUT_PATH)
    auth_url_params = urlencode({
        "client_id": settings.FUSIONAUTH_CLIENT_ID,
        "tenant_id": settings.FUSIONAUTH_TENANT_ID,
        "post_logout_redirect_uri": settings.FUSIONAUTH_REDIRECT_URL,
    })
    auth_url = f"{base_auth_url}?{auth_url_params}"
    return HttpResponseRedirect(auth_url)