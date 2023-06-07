from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm as DjangoUserAdminForm
from django.utils.translation import gettext_lazy as _

from safers.core.widgets import DataListWidget, JSONWidget
from safers.users.models import User, ProfileDirection, Organization, Role

###########
# filters #
###########


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


#########
# forms #
#########


class UserAdminForm(DjangoUserAdminForm):
    """
    Custom form w/ some pretty fields; formats the profile
    and lets me choose from valid Organizations & Roles
    """
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organization_name"].help_text = _(
            "The name of the organization this user belongs to."
        )
        self.fields["organization_name"].widget = DataListWidget(
            name="organization_name",
            options=[
                organization.name for organization in Organization.objects.all()
            ],
        )
        self.fields["role_name"].help_text = _(
            "The name of the role this user belongs to."
        )
        self.fields["role_name"].widget = DataListWidget(
            name="role_name",
            options=[role.name for role in Role.objects.all()],
        )
        self.fields["profile"].widget = JSONWidget()


##########
# admins #
##########


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    actions = (
        "toggle_accepted_terms",
        "synchronize_profiles_local_to_remote",
        "synchronize_profiles_remote_to_local",
    )
    model = User
    form = UserAdminForm
    add_fieldsets = ((
        None,
        {
            "classes": ("wide", ),
            "fields": (
                "email",
                "password1",
                "password2",
                "accepted_terms",
                "change_password",
                "status",
            )
        }
    ))
    fieldsets = (
        (
            None, {
                "fields": (
                    "id",
                    "auth_id",
                    "email",
                    "username",
                    "password",
                )
            }
        ),
        (
            _("General Info"), {
                "fields": (
                    "status",
                    "change_password",
                    "accepted_terms",
                )
            }
        ),
        (
            _("Permissions"),
            {
                "classes": ("collapse", ),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            }
        ),
        (
            _("Important Dates"),
            {
                "classes": ("collapse", ),
                "fields": (
                    "last_login",
                    "date_joined",
                )
            }
        ),
        (
            _("Safers"),
            {
                "fields": (
                    "organization_name",
                    "role_name",
                    "profile",
                    "default_aoi",
                    "favorite_alerts",
                    "favorite_events",
                    "favorite_camera_medias",
                )
            }
        ),
    )
    filter_horizontal = (
        "groups",
        "user_permissions",
        "favorite_alerts",
        "favorite_events",
        "favorite_camera_medias",
    )
    list_display = (
        "email",
        "is_staff",
        "is_active",
        "accepted_terms",
        "status",
        "get_authentication_type_for_list_display",
        "organization_name",
        "role_name",
    )
    list_filter = (
        LocalOrRemoteFilter,
        "status",
        "organization_name",
        "role_name",
    ) + DjangoUserAdmin.list_filter
    readonly_fields = (
        "id",
        "auth_id",
    ) + DjangoUserAdmin.readonly_fields

    @admin.display(description="AUTHENTICATION TYPE")
    def get_authentication_type_for_list_display(self, instance):
        authentication_type = "unknown"
        if instance.is_local:
            authentication_type = "local"
        elif instance.is_remote:
            authentication_type = "remote"
        return authentication_type

    @admin.display(
        description="Toggles the term acceptance of the selected users"
    )
    def toggle_accepted_terms(self, request, queryset):
        # TODO: doing this cleverly w/ negated F expressions is not supported (https://code.djangoproject.com/ticket/16211)
        # queryset.update(accepted_terms=not(F("accepted_terms")))
        for obj in queryset:
            obj.accepted_terms = not obj.accepted_terms
            obj.save()

            msg = f"{obj} {'has not' if not obj.accepted_terms else 'has'} accepted terms."
            self.message_user(request, msg)

    @admin.display(
        description=
        "Synchronize the selected users profiles from the DASHBOARD to the GATEWAY."
    )
    def synchronize_profiles_local_to_remote(self, request, queryset):
        self.synchronize_profiles(
            request, queryset, direction=ProfileDirection.LOCAL_TO_REMOTE
        )

    @admin.display(
        description=
        "Synchronize the selected users profiles from the GATEWAY to the DASHBOARD."
    )
    def synchronize_profiles_remote_to_local(self, request, queryset):
        self.synchronize_profiles(
            request, queryset, direction=ProfileDirection.REMOTE_TO_LOCAL
        )

    def synchronize_profiles(self, request, queryset, direction=None):
        for obj in queryset:
            auth_token = obj.access_tokens.unexpired().first()
            if auth_token:
                try:
                    obj.synchronize_profile(auth_token.token, direction)
                    obj.save()
                    msg = f"{obj} has updated their profile."
                    msg_level = messages.SUCCESS
                except Exception as exception:
                    msg = f"{obj} failed to update their profile."
                    msg_level = messages.ERROR
            else:
                msg = f"{obj} cannot update their profile; no tokens are available."
                msg_level = messages.WARNING

            self.message_user(request, msg, level=msg_level)
