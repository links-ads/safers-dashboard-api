from django.contrib import admin

from safers.core.models import Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    ordering = ("admin_name", )
    search_fields = ("admin_name", )
