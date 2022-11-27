
import pytest
from custom_components.blaueberg.packet.expanding_section import *
from custom_components.blaueberg.packet.errors import *


def test_expanding_section_init():
    ExpandingSection()


@pytest.mark.parametrize(
    "new_value,expected", [
        (bytes([0xFF]), 0xFF),
        (bytes([0xFF, 0x11]), 0xFF11),
        (bytes([0x0, 0x0, 0x11]), 0x11),
        (bytes([0xDD, 0xFF, 0x11]), 0xDDFF11)
    ]
)
def test_section_set_bytes(new_value: bytes, expected: int):
    assert ExpandingSection().set_bytes(new_value).value == expected


@pytest.mark.parametrize(
    "new_value,expected", [
        (bytes([0xFF]), 0xFF),
        (bytes([0xFF, 0x11]), 0xFF11),
        (bytes([0xFF, 0x11, 0x22]), 0xFF1122)
    ]
)
def test_section_partial_decode(new_value: bytes, expected: int):
    s = ExpandingSection()
    assert s.partial_decode(new_value) == bytes()
    assert s.value == expected
