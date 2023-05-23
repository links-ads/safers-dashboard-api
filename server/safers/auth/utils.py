from rest_framework.settings import settings as drf_settings


def reshape_auth_errors(auth_error_response):
    """
    Tries to reshape errors from FusionAuth into a format suitable for
    DRF
    """
    drf_error_response = {}
    field_errors = auth_error_response.get("fieldErrors")
    non_field_errors = None  # TODO
    if field_errors or non_field_errors:
        drf_error_response.update({
            field: [error.get("message") for error in errors]
            for field,
            errors in field_errors.items()
        })
        return drf_error_response

    return auth_error_response