import pytest

from safers.core.models import SafersSettings


@pytest.fixture
def safers_settings():
    safers_settings = SafersSettings.load()
    return safers_settings