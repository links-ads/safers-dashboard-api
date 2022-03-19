from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from safers.users.forms import UserCreationForm, UserChangeForm
from safers.users.models import User


class LocalOrRemoteFilter(admin.SimpleListFilter):
    title = "authentication type"
    parameter_name = "_ignore"  # ignoring parameter_name and computing qs manually

    def lookups(self, request, model_admin):
        return (
            ("_is_local", _("Local")),
            ("_is_remote", _("Remote")),
        )

    def queryset(self, request, qs):
        value = self.value()
        if value:
            qs = qs.filter(**{value: True})
        return qs


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    actions = (
        "toggle_accepted_terms",
        "toggle_verication",
    )
    model = User
    add_form = UserCreationForm
    form = UserChangeForm
    fieldsets = (
        (None, {"fields": ["id", "auth_id", "username", "email", "password"]}),
        ("Personal Info", {"fields": ["first_name", "last_name", "role", "organization",]}),
        ("Permissions", {"fields": ["is_active", "is_staff","is_superuser", "accepted_terms","groups", "user_permissions"] }),
        ("Important Dates", {"fields": ["last_login", "date_joined"]}),
        ("Safers", {"fields": ["default_aoi", "favorite_alerts", "favorite_events"]}),
    )  # yapf: disable
    filter_horizontal = (
        "groups",
        "user_permissions",
        "favorite_alerts",
        "favorite_events",
    )
    list_display = [
        "email",
        "id",
        "is_verified_for_list_display",
        "accepted_terms",
        "role",
        "organization",
        "get_authentication_type_for_list_display",
    ]
    list_filter = (
        LocalOrRemoteFilter,
        "role",
        "organization",
    ) + auth_admin.UserAdmin.list_filter
    readonly_fields = (
        "id",
        "auth_id",
    ) + auth_admin.UserAdmin.readonly_fields

    def toggle_accepted_terms(self, request, queryset):
        # TODO: doing this cleverly w/ negated F expressions is not supported (https://code.djangoproject.com/ticket/16211)
        # queryset.update(accepted_terms=not(F("accepted_terms")))
        for obj in queryset:
            obj.accepted_terms = not obj.accepted_terms
            obj.save()

            msg = f"{obj} {'has not' if not obj.accepted_terms else 'has'} accepted terms."
            self.message_user(request, msg)

    toggle_accepted_terms.short_description = (
        "Toggles the term acceptance of the selected users"
    )

    def toggle_verication(self, request, queryset):

        for obj in queryset:

            emailaddress, created = obj.emailaddress_set.get_or_create(
                user=obj, email=obj.email
            )
            if not emailaddress.primary:
                emailaddress.set_as_primary(conditional=True)

            emailaddress.verified = not emailaddress.verified
            emailaddress.save()

            msg = f"{emailaddress} {'created and' if created else ''} {'not' if not emailaddress.verified else ''} verified."
            self.message_user(request, msg)

    toggle_verication.short_description = (
        "Toggles the verification of the selected users' primary email addresses"
    )

    def is_verified_for_list_display(self, instance):
        return instance.is_verified

    is_verified_for_list_display.boolean = True
    is_verified_for_list_display.short_description = "IS VERIFIED"

    def get_authentication_type_for_list_display(self, instance):
        if instance.is_local:
            return "local"
        elif instance.is_remote:
            return "remote"

    get_authentication_type_for_list_display.short_description = "AUTHENTICATION TYPE"
