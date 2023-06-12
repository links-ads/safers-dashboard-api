"""
Concrete generic views that do everything the standard DRF views do except for
patch / partial_update
"""
from rest_framework import generics, mixins


class PatchlessUpdateModelMixin(object):
    """
    exposes an update (put) but not a partial_update (patch)
    """
    def update(self, request, *args, **kwargs):
        return mixins.UpdateModelMixin.update(self, request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save()


class PatchlessUpdateAPIView(
    PatchlessUpdateModelMixin,
    generics.GenericAPIView,
):
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class RetrievePatchlessUpdateAPIView(
    mixins.RetrieveModelMixin,
    PatchlessUpdateModelMixin,
    generics.GenericAPIView,
):
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class RetrievePatchlessUpdateDestroyAPIView(
    mixins.RetrieveModelMixin,
    PatchlessUpdateModelMixin,
    mixins.DestroyModelMixin,
    generics.GenericAPIView,
):
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)