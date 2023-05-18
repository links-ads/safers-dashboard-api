from django.dispatch import Signal, receiver

# generic signal that geometries send to parents when their geometry updates
# in order to allow parents to update their center & bounding_box & etc.

geometry_updated = Signal()#providing_args=["geometry", "parent"])


@receiver(geometry_updated)
def geometry_updated_handler(sender, *args, **kwargs):
    """
    If any of the geometries have been updated,
    then the center/bounding box of the parent should be recalculated
    """
    geometery = kwargs["geometry"]
    parent = kwargs["parent"]
    parent.recalculate_geometries(force_save=True)
