from rest_framework.serializers import CurrentUserDefault

class ContextVariableDefault(object):
    """
    May be applied as a `default=...` value on a serializer field
    Returns the "variable_name" item from the serializer context.
    Raise an error on a missing item only if "raise_error" is True.
    """

    requires_context = True

    def __init__(self, variable_name, raise_error=False):
        self.variable_name = variable_name
        self.raise_error = raise_error

    def __call__(self, serializer_field):
        try:
            return serializer_field.context[self.variable_name]
        except KeyError as e:
            if self.raise_error:
                raise e


class SwaggerCurrentUserDefault(CurrentUserDefault):
    """
    swagger doesn't play nicely w/ CurrentUserDefault:
    Firstly, it doesn't pass 'serializer_field' to default().
    Secondly, it might fail if using a 'slug_field' that doesn't exist on AnonymousUser.
    """
   
    def __call__(self, serializer_field=None):
        if serializer_field is not None:
            view = serializer_field.context.get("view")
            if not getattr(view, "swagger_fake_view", False):
                return super().__call__(serializer_field)
        return None