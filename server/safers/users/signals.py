# from django.contrib.auth import get_user_model
# from django.db.models.signals import post_save, post_delete

# from safers.users.models import UserProfile


# def post_save_user_hander(sender, *args, **kwargs):
#     """
#     If a local user has just been created,
#     then the corresponding profile must also be created.
#     """

#     created = kwargs.get("created", False)
#     instance = kwargs.get("instance", None)
#     if created and instance:
#         UserProfile.objects.create(local_user=instance)


# post_save.connect(
#     post_save_user_hander,
#     sender=get_user_model(),
#     dispatch_uid="post_save_user_handler",
# )
