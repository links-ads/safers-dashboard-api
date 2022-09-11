import json

from django.conf import settings
from django.http import HttpResponse


class JSONDebugToolbarMiddleware:
    """
    The Django Debug Toolbar usually only works for views that return HTML.
    This middleware wraps any JSON response in HTML if the request
    has a 'debug-toolbar' query parameter (e.g. http://localhost/foo?debug-toolbar)
    """

    QUERY_PARAMETER = "debug-toolbar"
    JSON_CONTENT_TYPE = "application/json"

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)
        if (
            self.QUERY_PARAMETER in request.GET and
            self.JSON_CONTENT_TYPE == response["Content-Type"]
        ):
            content = json.dumps(json.loads(response.content), indent=2)
            response = HttpResponse(
                f"<html><body><pre>{content}</pre></body></html>"
            )

        return response
