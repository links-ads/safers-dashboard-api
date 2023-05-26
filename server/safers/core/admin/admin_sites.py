from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from django.urls import reverse
from django.utils.html import format_html

from safers.core.models import SiteProfile


class SiteProfileAdminForm(ModelForm):
    class Meta:
        model = SiteProfile
        fields = (
            "site",
            "description",
            "code",
            "show_admin_notice",
            "admin_notice_color",
        )

    def clean_code(self):
        from safers.data.models.models_maprequests import REQUEST_ID_SEPARATOR
        code = self.cleaned_data.get("code")
        if code and REQUEST_ID_SEPARATOR in code:
            raise ValidationError(
                f"code cannot include the character: '{REQUEST_ID_SEPARATOR}'."
            )
        return code


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    form = SiteProfileAdminForm
    list_display = (
        "get_name_for_list_display",
        "code",
        "get_site_for_list_display",
    )

    @admin.display(description="PROFILE")
    def get_name_for_list_display(self, obj):
        return str(obj.site.name)

    @admin.display(description="SITE")
    def get_site_for_list_display(self, obj):
        # not using "get_clickable_fk_for_list_display"
        # b/c the Site Model uses a non-standard admin change URL
        site = obj.site
        admin_change_url_name = "admin:sites_site_change"
        list_display = f"<a href='{reverse(admin_change_url_name, args=[site.pk])}'>{str(site)}</a>"
        return format_html(list_display)