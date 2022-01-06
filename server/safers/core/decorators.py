import functools

def conditional_exception(conditional, exception):
    """
    A decorator for a view that raises an exception if conditional is true.
    Typical usage is:
    >>> @method_decorator(
    >>>     conditional_exception(
    >>>         lambda request: <whatever>...,
    >>>         APIException(),
    >>>     ),
    >>>     name="get"
    >>> )
    """

    def _decorator(view_fn):
        @functools.wraps(view_fn)
        def _wrapper(request, *args, **kwargs):

            if conditional(request):
                raise exception
            return view_fn(request, *args, **kwargs)

        return _wrapper

    return _decorator


def swagger_fake(fake_retval=None):
    """
    A decorator for a view that returns the provided value
    if being run in the context of swagger schema generation;
    (as per https://github.com/axnsan12/drf-yasg/issues/333#issuecomment-474883875)
    This is intended to be applied to "get_queryset" and/or "get_object"
    """
    def _decorator(view_fn):
        @functools.wraps(view_fn)
        def _wrapper(*args, **kwargs):

            if not args:
                # if this decorator is applied to a CBV using "method_decorator",
                # then view_fn will actually be an instance of functools.partial;
                # I have to introspect it to get the view it was called w/
                _self = view_fn.func.__self__
            else:
                # if this decorator is applied directly to a fn,
                # then the 1st argument will be the view it was called w/
                _self = args[0]

            if getattr(_self, "swagger_fake_view", False):
                return fake_retval

            return view_fn(*args, **kwargs)

        return _wrapper

    return _decorator
