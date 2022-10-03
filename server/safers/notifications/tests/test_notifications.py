import pytest
import urllib

from django.urls import resolve, reverse

from rest_framework import status

from safers.notifications.models import Notification, NotificationScopeChoices, NotificationRestrictionChoices

from safers.core.tests.factories import *
from safers.users.tests.factories import *
from safers.notifications.tests.factories import *


@pytest.mark.django_db
class TestNotificationModels:
    def test_filter_by_user(self):

        user = UserFactory()
        organization_1 = OrganizationFactory()
        organization_2 = OrganizationFactory()
        citizen_role = RoleFactory(name="citizen")
        non_citizen_role = RoleFactory(name="professional")

        unspecified_notification = NotificationFactory(
            description="unspecified",
            scope=None,
            restriction=None,
        )
        public_notificiation = NotificationFactory(
            description="public",
            scope=NotificationScopeChoices.PUBLIC,
            restriction=None,
        )
        restricted_citizen_notificiation = NotificationFactory(
            description="restricted_citizen",
            scope=NotificationScopeChoices.RESTRICTED,
            restriction=NotificationRestrictionChoices.CITIZEN,
        )
        restricted_professional_notificiation = NotificationFactory(
            description="restricted_professional",
            scope=NotificationScopeChoices.RESTRICTED,
            restriction=NotificationRestrictionChoices.PROFESSIONAL,
        )
        restricted_organization_notificiation = NotificationFactory(
            description="restricted_organization",
            scope=NotificationScopeChoices.RESTRICTED,
            restriction=NotificationRestrictionChoices.ORGANIZATION,
            target_organizations=[organization_1],
        )

        assert Notification.objects.count() == 5

        public_qs = Notification.objects.filter_by_user(user)
        assert public_qs.count() == 2
        assert unspecified_notification in public_qs
        assert public_notificiation in public_qs

        user.role = citizen_role
        user.save()
        citizen_qs = Notification.objects.filter_by_user(user)
        assert citizen_qs.count() == 3
        assert unspecified_notification in citizen_qs
        assert public_notificiation in citizen_qs
        assert restricted_citizen_notificiation in citizen_qs

        user.role = non_citizen_role
        user.save()
        professional_qs = Notification.objects.filter_by_user(user)
        assert professional_qs.count() == 3
        assert unspecified_notification in professional_qs
        assert public_notificiation in professional_qs
        assert restricted_professional_notificiation in professional_qs

        user.organization = organization_2  # (note that this is the _wrong_ organization to match the query)
        user.save()
        organization_qs = Notification.objects.filter_by_user(user)
        assert organization_qs.count() == 3
        assert unspecified_notification in organization_qs
        assert public_notificiation in organization_qs
        assert restricted_professional_notificiation in organization_qs

        user.organization = organization_1  # (note that this is the _right_ organization to match the query)
        user.save()
        organization_qs = Notification.objects.filter_by_user(user)
        assert organization_qs.count() == 4
        assert unspecified_notification in organization_qs
        assert public_notificiation in organization_qs
        assert restricted_professional_notificiation in organization_qs
        assert restricted_organization_notificiation in organization_qs


@pytest.mark.django_db
class TestNotificationViews:
    def test_bbox_filter(self, remote_user, api_client):

        notification = NotificationFactory()
        (xmin, ymin, xmax,
         ymax) = notification.geometries.first().geometry.extent

        client = api_client(remote_user)

        in_bounding_box = [xmin, ymin, xmax, ymax]
        out_bounding_box = [
            xmin + (xmax - xmin) + 1,
            ymin + (ymax - ymin) + 1,
            xmax + (xmax - xmin) + 1,
            ymax + (ymax - ymin) + 1,
        ]

        url_params = urllib.parse.urlencode({
            "bbox": ",".join(map(str, in_bounding_box))
        })
        url = f"{reverse('notifications-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 1

        url_params = urllib.parse.urlencode({
            "bbox": ",".join(map(str, out_bounding_box))
        })
        url = f"{reverse('notifications-list')}?{url_params}"
        response = client.get(url, format="json")
        assert status.is_success(response.status_code)

        content = response.json()
        assert len(content) == 0
