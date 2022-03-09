from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from safers.users.forms import UserCreationForm, UserChangeForm
from safers.users.models import User


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    actions = (
        "toggle_accepted_terms",
        "toggle_verication",
    )
    model = User
    add_form = UserCreationForm
    form = UserChangeForm
    fieldsets = ((None, {
        "fields": ("id", "auth_id", "username", "password")
    }), ) + auth_admin.UserAdmin.fieldsets[1:]
    list_display = [
        "email",
        "id",
        "is_verified_for_list_display",
        "accepted_terms",
    ]
    # list_filter =  ("organization", ) + auth_admin.UserAdmin.list_filter
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


# class CalculatedFieldFilter(admin.SimpleListFilter):

#     lookup_values_map = {
#         # map of qs lookup values to filter values
#         True: ("yes", _("Yes")),
#         False: ("no", _("No")),
#     }

#     def lookups(self, request, model_admin):
#         return self.lookup_values_map.values()

#     def queryset(self, request, qs):
#         value = self.value()
#         for k, v in self.lookup_values_map.items():
#             if value == v[0]:
#                 return qs.filter(**{self.parameter_name: k})
#         return qs

# class IsLocalFilter(CalculatedFieldFilter):
#     parameter_name = title = "is_local"

# class IsRemoteFilter(CalculatedFieldFilter):
#     parameter_name = title = "is_remote"

# class UserProfileAdminForm(ModelForm):
#     class Meta:
#         model = UserProfile
#         fields = "__all__"

#     def clean(self):
#         """
#         Check a UserProfile's constraints during cleaning
#         """

#         cleaned_data = super().clean()

#         data = UserProfileSerializer(self.instance).data
#         data.update(cleaned_data)

#         if not bool(data["local_user"]) ^ bool(data["auth_id"]):
#             raise ValidationError("UserProfile must have either a local user or a remote (auth_id) user.")

#         return cleaned_data

# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     fields = (
#         "auth_id",
#         # "local_user",
#         # "is_active",
#     )
#     form = UserProfileAdminForm
#     list_display = (
#         # "user",
#     )
#     list_filter = (
#         IsLocalFilter,
#         IsRemoteFilter,
#     )
#     readonly_fields = (
#         "auth_id",
#     )
