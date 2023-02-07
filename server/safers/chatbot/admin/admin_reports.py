from django.contrib import admin

from safers.chatbot.models import ReportCategory


@admin.register(ReportCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "category_id",
        "group",
        "sub_group",
        "name",
    )
    list_filter = (
        "group",
        "sub_group",
    )
