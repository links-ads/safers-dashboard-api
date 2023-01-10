from django.db.models.signals import post_save, post_delete

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


def post_delete_camera_media_handler(sender, *args, **kwargs):
    """
    If a CamerMedia is being deleted,
    then the corresponding camera might need to be updated as well.
    Additionally, any associated files should be deleted.
    """
    camera_media = kwargs.get("instance", None)
    if camera_media:
        camera_media.camera.recalculate_last_update(ignore=[camera_media])
        camera_media_file = camera_media.file
        if camera_media_file:
            camera_media_file.delete(save=False)


post_delete.connect(
    post_delete_camera_media_handler,
    sender=CameraMedia,
    dispatch_uid="safers_post_delete_camera_media_handler",
)
