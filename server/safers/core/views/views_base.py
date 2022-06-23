# from django.contrib.auth import get_user_model
# from django.core.exceptions import ValidationError

# from rest_framework import exceptions as rest_exceptions

from rest_framework import mixins
from rest_framework import viewsets


class CannotDeleteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    A viewset that excludes the `delete` action.
    """
    pass


# def get_error_message(exc) -> str:
#     if hasattr(exc, 'message_dict'):
#         return exc.message_dict
#     error_msg = get_first_matching_attr(exc, 'message', 'messages')

#     if isinstance(error_msg, list):
#         error_msg = ', '.join(error_msg)

#     if error_msg is None:
#         error_msg = str(exc)

#     return error_msg

# class ApiErrorsMixin:
#     """
#     Mixin that transforms Django and Python exceptions into rest_framework ones.
#     Without the mixin, they return 500 status code which is not desired.
#     """
#     expected_exceptions = {
#         ValueError: rest_exceptions.ValidationError,
#         ValidationError: rest_exceptions.ValidationError,
#         PermissionError: rest_exceptions.PermissionDenied,
#         get_user_model().DoesNotExist: rest_exceptions.NotAuthenticated
#     }

#     def handle_exception(self, exc):
#         if isinstance(exc, tuple(self.expected_exceptions.keys())):

#             if hasattr(exc, 'message_dict'):
#                 error_msg = exc.message_dict

#             error_msg = get_first_matching_attr(exc, 'message', 'messages')

#             if isinstance(error_msg, list):
#                 error_msg = ', '.join(error_msg)

#             if error_msg is None:
#                 error_msg = str(exc)

#             drf_exception_class = self.expected_exceptions[exc.__class__]
#             drf_exception = drf_exception_class(error_msg)

#             return super().handle_exception(drf_exception)

#         return super().handle_exception(exc)