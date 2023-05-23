from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm as DjangoUserAdminForm
from django.utils.translation import gettext_lazy as _

from safers.core.widgets import DataListWidget, JSONWidget
from safers.users.models import User, Organization, Role

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
        "toggle_verication",
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
                "change_password",  # "status",
            )
        }
    ))
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "auth_id",
                    "email",
                    "username",
                    "password",
                    "active_token_key",
                )
            }
        ),
        (
            _("General Info"), {
                "fields": (
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
        "is_verified_for_list_display",
        "get_authentication_type_for_list_display",
        "organization_name",
        "role_name",
    )
    list_filter = (
        LocalOrRemoteFilter,  # "status",
        "organization_name",
        "role_name",
    ) + DjangoUserAdmin.list_filter
    readonly_fields = (
        "id",
        "auth_id",
        "active_token_key",
    ) + DjangoUserAdmin.readonly_fields

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

    @admin.display(boolean=True, description="IS VERIFIED")
    def is_verified_for_list_display(self, instance):
        return instance.is_verified

    @admin.display(description="AUTHENTICATION TYPE")
    def get_authentication_type_for_list_display(self, instance):
        authentication_type = "unknown"
        if instance.is_local:
            authentication_type = "local"
        elif instance.is_remote:
            authentication_type = "remote"
        return authentication_type
