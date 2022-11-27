
import pytest
from custom_components.blaueberg.packet.dynamic_section import *
from custom_components.blaueberg.packet.errors import *


@pytest.mark.parametrize(
    "length_byte_size", [(1), (2)]
)
def test_dynamic_section_init(length_byte_size: int):
    DynamicSection(length_byte_size)


@pytest.mark.parametrize(
    "length_byte_size,exception", [
        (-1, byte_size_error), (0, byte_size_error)]
)
def test_dynamic_section_init_with_exception(length_byte_size: int, exception: Exception):
    with pytest.raises(type(exception)) as exc_info:
        DynamicSection(length_byte_size)
    assert str(exception) == str(exc_info.value)


@pytest.mark.parametrize(
    "new_value,expected_value,expected_byte_size", [
        (bytes([0xFF]), 0xFF, 1), (bytes([0xFF, 0x11]), 0xFF11, 2)]
)
def test_dynamic_section_set_bytes(new_value: bytes, expected_value: int, expected_byte_size: int):
    section = DynamicSection().set_bytes(new_value)
    assert section.value == expected_value
    assert section.byte_size == expected_byte_size


@pytest.mark.parametrize(
    "new_value,expected_value,expected_byte_size", [
        (bytes([0xFF]), 0xFF, 1), (bytes([0xFF, 0x11]), 0xFF11, 2)]
)
def test_dynamic_section_set_bytes_trailing_zeros(new_value: bytes, expected_value: int, expected_byte_size: int):
    section = DynamicSection(trail_or_lead=Zeros.TRAILING).set_bytes(new_value)
    assert section.value == expected_value
    assert section.byte_size == expected_byte_size


@pytest.mark.parametrize(
    "length_byte_size,value,exception", [
        (1, bytes([1 for _ in range(0xFF+1)]), value_overflow_error)]
)
def test_dynamic_section_set_bytes_with_exception(length_byte_size: int, value: bytes, exception: Exception):
    with pytest.raises(type(exception)) as exc_info:
        DynamicSection(length_byte_size).set_bytes(value)
    assert str(exception) == str(exc_info.value)


@pytest.mark.parametrize(
    "length_byte_size,value,expected", [
        (1, bytes([0]), bytes([1, 0])),
        (1, bytes([1]), bytes([1, 1])),
        (2, bytes([0]), bytes([0, 1, 0])),
        (2, bytes([1, 2, 3, 4]), bytes([0, 4, 1, 2, 3, 4]))]
)
def test_dynamic_section_to_bytes(length_byte_size: int, value: bytes, expected: bytes):
    assert DynamicSection(length_byte_size).set_bytes(
        value).to_bytes() == expected


@pytest.mark.parametrize(
    "length_byte_size,input,output,expected", [
        (1, bytes([0]), bytes(), DynamicSection()), (1, bytes(
            [0x02, 0x01, 0x03]), bytes(), DynamicSection().set_bytes(bytes([0x01, 0x03]))),
        (2, bytes([0x0, 0x02, 0x01, 0x03, 0x04]), bytes([0x04]),
         DynamicSection(2).set_bytes(bytes([0x01, 0x03]))),
        (1, bytes([0x03, 0x02, 0x01]), bytes(), DynamicSection().set_bytes(bytes([0x02, 0x01, 0x00])))]
)
def test_dynamic_section_partial_decode(length_byte_size: int, input: bytes, output: bytes, expected: DynamicSection):
    ds = DynamicSection(length_byte_size)
    assert ds.partial_decode(input) == output
    assert ds == expected
