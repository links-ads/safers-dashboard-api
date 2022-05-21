from django.db.models.signals import post_save, pre_delete

from safers.cameras.models import CameraMedia


def post_save_camera_media_handler(sender, *args, **kwargs):
    """
    If a CamerMedia has just been updated,
    then the corresponding camera might need to be updated as well.
    """
    camera_media = kwargs.get("instance", None)
    if camera_media:
        camera_media.camera.recalculate_last_update()


post_save.connect(
    post_save_camera_media_handler,
    sender=CameraMedia,
    dispatch_uid="safers_post_save_camera_media_handler",
)


def pre_delete_camera_media_handler(sender, *args, **kwargs):
    """
    If a CamerMedia is about to be deleted,
    then the corresponding camera might need to be updated as well.
    """
    camera_media = kwargs.get("instance", None)
    if camera_media:
        camera_media.camera.recalculate_last_update(ignore=[camera_media])


pre_delete.connect(
    pre_delete_camera_media_handler,
    sender=CameraMedia,
    dispatch_uid="safers_pre_delete_camera_media_handler",
)
