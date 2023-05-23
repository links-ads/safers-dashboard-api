"""
Custom Authentication Extensions to ensure DRF Authentication is correctly configured in swagger.
drf-spectacular looks at `settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] to try and 
automatically populate the "Available Authorizations" Dialog Box.  But if any of those classes are
not recognized, or if orbison's implementation of them is non-standard, then these schemes can be
used instead (as long as the "target_class" matches and "priority" is <= any other matching schemes).

(see: https://drf-spectacular.readthedocs.io/en/latest/faq.html#where-should-i-put-my-extensions-my-extensions-are-not-detected)
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object

from safers.auth.authentication import OAuth2Authentication


class SwaggerOAuth2AuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Simple token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Bearer ".  For example:

        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
    """

    # TODO: FOUND A BUG IN drf-spectacular (`target_class` requires Class object instead of path) ?
    # taget_class = "safers.auth.authentication.OAuth2Authentication"
    target_class = OAuth2Authentication
    name = "access_token Authentication"
    match_subclasses = False
    priority = -1

    token_prefix = "Bearer"
    description = f"Token-based authentication with required prefix: {token_prefix}"

    def get_security_definition(self, auto_schema):
        scheme = build_bearer_security_scheme_object(
            header_name="Authorization", token_prefix=self.token_prefix
        )
        scheme["description"] = self.description
        return scheme
