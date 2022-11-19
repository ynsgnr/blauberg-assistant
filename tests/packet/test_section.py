
import pytest
from custom_components.blaueberg.packet import *

@pytest.mark.parametrize(
    "value,byte_size,exception", [
        (0, -1, byte_size_error), (0x111, 1, value_overflow_error)]
)
def test_section_init_with_exception(value: int, byte_size: int, exception: Exception):
    with pytest.raises(type(exception)) as exc_info:
        Section(value, byte_size)
    assert str(exception) == str(exc_info.value)


@pytest.mark.parametrize(
    "value,byte_size", [(0, 0), (0, 1), (0x11, 1), (0xFF, 1), (0x1FFF, 2)]
)
def test_section_init(value: int, byte_size: int):
    Section(value, byte_size)


@pytest.mark.parametrize(
    "new_value,byte_size,expected", [(bytes([0xFF]), 1, 0xFF), (bytes([0xFF, 0x11]), 3, 0xFF11), (bytes([
        0x0, 0x0, 0x11]), 3, 0x11), (bytes([0x0, 0x0, 0x0, 0x11]), 3, 0x11)]
)
def test_section_set_bytes(new_value: bytes, byte_size: int, expected: int):
    assert Section(0, byte_size).set_bytes(new_value).value == expected


@pytest.mark.parametrize(
    "new_value,byte_size,exception", [
        (bytes([0xFF, 0x11]), 1, value_overflow_error)]
)
def test_section_set_bytes_with_exception(new_value: bytes, byte_size: int, exception: Exception):
    with pytest.raises(type(exception)) as exc_info:
        Section(0, byte_size).set_bytes(new_value)
    assert str(exception) == str(exc_info.value)


@pytest.mark.parametrize(
    "value,byte_size,expected", [(0, 0, bytes([0])), (0, 1, bytes([0])), (0x11, 1, bytes(
        [0x11])), (0x1FFF, 2, bytes([0x1F, 0xFF])), (0x1FFF, 3, bytes([0x0, 0x1F, 0xFF]))]
)
def test_section_to_bytes(value: int, byte_size: int, expected: bytes):
    assert Section(value, byte_size).to_bytes() == expected

