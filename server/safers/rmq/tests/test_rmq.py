import pytest
import re

from safers.rmq.rmq import *


class TestRMQBindingKeys:
    def test_routing_key_regex(self):

        routing_key = "some.test.key"

        pattern1 = "some.#"  # match anything
        pattern2 = "some.*.key"  # match single section, then specific text
        pattern3 = "some.*.#"  # match single section, then anything
        pattern4 = "some.*"  # match single section only (should FAIL)
        pattern5 = "some.#key"  # match anything, then specific text
        pattern6 = "some.#fail"  # match wrong text (should FAIL)

        assert re.match(binding_key_to_regex(pattern1), routing_key) is not None
        assert re.match(binding_key_to_regex(pattern2), routing_key) is not None
        assert re.match(binding_key_to_regex(pattern3), routing_key) is not None
        assert re.match(binding_key_to_regex(pattern4), routing_key) is None
        assert re.match(binding_key_to_regex(pattern5), routing_key) is not None
        assert re.match(binding_key_to_regex(pattern6), routing_key) is None
