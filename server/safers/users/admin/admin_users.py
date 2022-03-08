from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from safers.users.forms import UserCreationForm, UserChangeForm
from safers.users.models import User


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    model = User
    add_form = UserCreationForm
    form = UserChangeForm
    fieldsets =((None, {"fields": ("id", "auth_id", "username", "password")}),) + auth_admin.UserAdmin.fieldsets[1:]    
    list_display = ["email", "id",]
    readonly_fields = ("id", "auth_id",) + auth_admin.UserAdmin.readonly_fields

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
