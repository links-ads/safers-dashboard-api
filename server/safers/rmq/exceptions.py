from rest_framework.exceptions import APIException


class RMQException(APIException):
    default_code = "error code"
    default_detail = "error detail"
    status_code = 401