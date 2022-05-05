from django.dispatch import receiver, Signal

geometry_updated = Signal(providing_args=["geometry", "parent"])


@receiver(geometry_updated)
def geometry_updated_handler(sender, *args, **kwargs):
    """
    If any of the geometries have been updated,
    then the center/bounding box of the parent should be recalculated
    """
    geometery = kwargs["geometry"]
    parent = kwargs["parent"]
    parent.recalculate_geometries(force_save=True)


# geometry_updated.connect(
#     alerts_geometry_updated_handler,
#     sender=AlertGeometry,
#     dispatch_uid="safers_alerts_geometry_updated_handler"
# )