from datetime import timedelta
import pytest

from django.utils import timezone

from safers.chatbot.models.models_communications import CommunicationStatusTypes, CommunicationScopeTypes, CommunicationRestrictionTypes
from safers.chatbot.serializers import CommunicationSerializer

from .factories import *


class TestCommunicationModel:
    def test_cannot_save(self):
        """
        checks that a communication cannot be saved
        """

        communication = CommunicationFactory.build()
        assert communication.pk is None
        with pytest.raises(NotImplementedError):
            communication.save()

    def test_status_property(self):

        communication = CommunicationFactory.build()

        communication.end_inclusive = True
        communication.end = timezone.now()
        assert communication.status == CommunicationStatusTypes.ONGOING

        communication.end_inclusive = False
        communication.end = timezone.now()
        assert communication.status == CommunicationStatusTypes.EXPIRED

        communication.end_inclusive = False
        communication.end = timezone.now() + timedelta(days=1)
        assert communication.status == CommunicationStatusTypes.ONGOING

        communication.end_inclusive = True
        communication.end = timezone.now() - timedelta(days=1)
        assert communication.status == CommunicationStatusTypes.EXPIRED

    def test_target_property(self):

        communication = CommunicationFactory.build()

        communication.scope = CommunicationScopeTypes.PUBLIC
        assert communication.target == CommunicationScopeTypes.PUBLIC

        communication.scope = CommunicationScopeTypes.RESTRICTED
        communication.restriction = CommunicationRestrictionTypes.CITIZEN
        assert communication.target == CommunicationRestrictionTypes.CITIZEN
