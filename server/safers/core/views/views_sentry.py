from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@permission_classes([AllowAny])
@api_view(["GET"])
def trigger_error(request):
    """
    a simple view that triggers an error
    (for testing sentry)
    """
    division_by_zero = 1 / 0
