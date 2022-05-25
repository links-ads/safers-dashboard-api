import pytest

from safers.core.utils import *


def test_case_insensitive_choices():
    class TestChoices(CaseInsensitiveTextChoices):
        TEST = "TEST", "Test"

    assert TestChoices.find_enum("TEST") == TestChoices.TEST
    assert TestChoices.find_enum("test") == TestChoices.TEST
    assert TestChoices.find_enum("TeSt") == TestChoices.TEST
    assert TestChoices.find_enum("invalid") == None