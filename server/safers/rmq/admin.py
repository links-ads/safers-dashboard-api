import json
import re

from django.contrib import admin, messages
from django.db.models import JSONField

from rest_framework.utils.encoders import JSONEncoder

from safers.core.admin import JSONAdminWidget

from .rmq import RMQ, BINDING_KEYS, binding_key_to_regex
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    actions = ("publish_messages", )
    fields = (
        "id",
        "timestamp",
        "name",
        "is_demo",
        "routing_key",
        "status",
        "body",
    )
    formfield_overrides = {JSONField: {"widget": JSONAdminWidget}}
    list_display = (
        "get_id_or_name_for_list_display",
        "timestamp",
        "routing_key",
        "status",
    )
    list_filter = (
        "status",
        "timestamp",
        "is_demo",
    )
    ordering = (
        "timestamp",
        "routing_key",
        "name",
    )
    readonly_fields = ("id", )
    search_fields = (
        "name",
        "routing_key",
    )

    @admin.display(description="ID or NAME")
    def get_id_or_name_for_list_display(self, obj):
        return obj.name or obj.id

    @admin.display(description="Publish Messages")
    def publish_messages(self, request, queryset):
        rmq = RMQ()

        for message in queryset:

            message_name_or_id = message.name or message.id

            try:

                rmq.publish(
                    json.dumps(message.body, cls=JSONEncoder),
                    message.routing_key,
                    str(message.id),
                )

            except Exception as e:
                msg = f"unable to publish message '{message_name_or_id}': {e}"
                self.message_user(request, msg, messages.ERROR)
                continue

            msg = f"sent message '{message_name_or_id}' to queue"
            self.message_user(request, msg, messages.INFO)

            unhandled_method = True
            for pattern, handlers in BINDING_KEYS.items():
                if re.match(binding_key_to_regex(pattern), message.routing_key):
                    unhandled_method = False
            if unhandled_method:
                msg = f"message '{message_name_or_id}' with routing_key '{message.routing_key}' will not be received by Dashbaord."
                self.message_user(request, msg, messages.WARNING)
