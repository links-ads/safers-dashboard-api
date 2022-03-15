from django.contrib import admin

from safers.users.models import Oauth2User


@admin.register(Oauth2User)
class Oauth2UserAdmin(admin.ModelAdmin):
    list_filter = ("user", )
    search_fields = ("user", )
