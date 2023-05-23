"""
Global URL Configuration
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.urls import include, path, re_path

from rest_framework import routers

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from safers.core.urls import (
    urlpatterns as core_urlpatterns,
    api_urlpatterns as core_api_urlpatterns,
)

from safers.rmq.urls import (
    urlpatterns as rmq_urlpatterns,
    api_urlpatterns as rmq_api_urlpatterns,
)

from safers.users.urls import (
    urlpatterns as users_urlpatterns,
    api_urlpatterns as users_api_urlpatterns,
)

from safers.aois.urls import (
    urlpatterns as aois_urlpatterns,
    api_urlpatterns as aois_api_urlpatterns,
)

from safers.alerts.urls import (
    urlpatterns as alerts_urlpatterns,
    api_urlpatterns as alerts_api_urlpatterns,
)

from safers.events.urls import (
    urlpatterns as events_urlpatterns,
    api_urlpatterns as events_api_urlpatterns,
)

from safers.cameras.urls import (
    urlpatterns as cameras_urlpatterns,
    api_urlpatterns as cameras_api_urlpatterns,
)

from safers.social.urls import (
    urlpatterns as social_urlpatterns,
    api_urlpatterns as social_api_urlpatterns,
)

from safers.chatbot.urls import (
    urlpatterns as chatbot_urlpatterns,
    api_urlpatterns as chatbot_api_urlpatterns,
)

from safers.data.urls import (
    urlpatterns as data_urlpatterns,
    api_urlpatterns as data_api_urlpatterns,
)

from safers.notifications.urls import (
    urlpatterns as notifications_urlpatterns,
    api_urlpatterns as notifications_api_urlpatterns,
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
swagger_restriction = user_passes_test(
    # prevent ordinary users from accessing swagger unless DEBUG is True
    lambda user: (settings.DEBUG or user.is_admin),
    login_url="admin:login",
)

api_schema_views = [
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
    path(
        "schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
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
api_urlpatterns += rmq_api_urlpatterns
api_urlpatterns += aois_api_urlpatterns
api_urlpatterns += alerts_api_urlpatterns
api_urlpatterns += events_api_urlpatterns
api_urlpatterns += cameras_api_urlpatterns
api_urlpatterns += social_api_urlpatterns
api_urlpatterns += chatbot_api_urlpatterns
api_urlpatterns += data_api_urlpatterns
api_urlpatterns += notifications_api_urlpatterns

#################
# normal routes #
#################

urlpatterns = [
    # profiling... 
    path("silk/", include('silk.urls', namespace="silk")),

    # django admin...
    path(settings.ADMIN_URL, admin.site.urls),


    # API...
    path("api/", include(api_urlpatterns)),
    # path("api/", silk_profile(include(api_urlpatterns)),

    # app-specific patterns (just in case)...
    path("", include(core_urlpatterns)),
    path("users/", include(users_urlpatterns)),
    path("messages/", include(rmq_urlpatterns)),
    path("aois/", include(aois_urlpatterns)),
    path("alerts/", include(alerts_urlpatterns)),
    path("events/", include(events_urlpatterns)),
    path("cameras/", include(cameras_urlpatterns)),
    path("social/", include(social_urlpatterns)),
    path("chatbot/", include(chatbot_urlpatterns)),
    path("data/", include(data_urlpatterns)),
    path("notifications/", include(notifications_urlpatterns)),
]

# local static & media files...
if settings.ENVIRONMENT == "development":
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
