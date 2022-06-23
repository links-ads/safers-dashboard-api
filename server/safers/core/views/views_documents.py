from django.http import FileResponse

from rest_framework import generics
from rest_framework import permissions
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

from safers.core.models import Document


class DocumentView(generics.RetrieveAPIView):
    """
    Returns a specific document
    """

    permission_classes = [permissions.AllowAny]
    queryset = Document.objects.active()
    lookup_field = "slug"
    lookup_url_kwarg = "document_slug"

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: "FileResponse"},
    )
    def get(self, request, *args, **kwargs):
        """
        Returns the file associated w/ this document
        """
        obj = self.get_object()
        response = FileResponse(obj.file)

        # if the request came from swagger I ought to make the document downloadable;
        # swagger doesn't cope nicely w/ displaying content in another tab
        if "api/swagger" in request.headers.get("referer", ""):
            content_disposition = response.headers.get(
                "Content-Disposition", None
            )
            if content_disposition is not None:
                response.headers["Content-Disposition"] = content_disposition.replace(
                    "inline", "attachment"
                )  # yapf: disable

        return response
