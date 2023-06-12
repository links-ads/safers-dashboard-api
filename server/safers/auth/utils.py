from rest_framework.settings import api_settings as drf_settings


def reshape_auth_errors(auth_error_response):
    """
    Tries to reshape errors from FusionAuth into a format suitable for
    DRF
    """
    drf_error_response = {}

    try:
        field_errors = auth_error_response.get("fieldErrors", [])
        if field_errors:
            drf_error_response.update({
                field: [error.get("message") for error in errors]
                for field,
                errors in field_errors.items()
            })

        non_field_errors = auth_error_response.get("error_description")
        if non_field_errors:
            drf_error_response[drf_settings.NON_FIELD_ERRORS_KEY
                              ] = non_field_errors
    except Exception:
        pass

    return drf_error_response or auth_error_response