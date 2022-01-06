"""
Global URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from rest_framework import permissions, routers

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from safers.core.urls import (
    urlpatterns as core_urlpatterns,
    api_urlpatterns as core_api_urlpatterns,
)

from safers.users.urls import (
    urlpatterns as users_urlpatterns,
    api_urlpatterns as users_api_urlpatterns,
)

################
# admin config #
################

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

#################
# swagger stuff #
#################

api_schema_view = get_schema_view(
   openapi.Info(
      title=f"{settings.PROJECT_NAME} API",
      default_version='v1',
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

api_schema_views = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', api_schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', api_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', api_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

##############
# API routes #
##############

api_router = routers.DefaultRouter()
api_urlpatterns = [
    path("", include(api_schema_views)),
    path("", include(api_router.urls)),
]
api_urlpatterns += core_api_urlpatterns
api_urlpatterns += users_api_urlpatterns

#################
# normal routes #
#################

urlpatterns = [
    # admin...
    path(settings.ADMIN_URL, admin.site.urls),

    # API...
    path("api/", include(api_urlpatterns)),

    # app-specific patterns...
    path("core/", include(core_urlpatterns)),
    path("users/", include(users_urlpatterns)),
 
]

# media files...
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
