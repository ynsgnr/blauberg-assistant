
import pytest
from custom_components.blaueberg.packet import *

value_overflow_error = OverflowError("value does not fit into the byte size")


@pytest.mark.parametrize(
    "value,byte_size,exception", [
        (0, -1, ValueError("byte_size can not be less than zero")), (0x111, 1, value_overflow_error)]
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


@pytest.mark.parametrize(
    "sections,expected", [([Section(0x1, 2), Section(0xF)], 0x010F), ([
        Section(0x1), Section(0x1FFF, 2)], 0x011FFF)]
)
def test_packet_to_int(sections: List[Section], expected: int):
    assert Packet(sections).to_int() == expected


@pytest.mark.parametrize(
    "sections,expected", [([Section(0x1, 2), Section(0xF)], bytes([0x0, 0x01, 0x0F])), ([
        Section(0x1), Section(0x1FFF, 2)], bytes([0x01, 0x1F, 0xFF]))]
)
def test_packet_to_bytes(sections: List[Section], expected: int):
    assert Packet(sections).to_bytes() == expected


@pytest.mark.parametrize(
    "sections,value,expected", [([Section.Template(2), Section.Template(1)], bytes(
        [0x0, 0x01, 0x0F]), [Section(0x1, 2), Section(0xF, 1)]), ([Section.Template(2), Section.Template(2)], bytes(
        [0x0, 0x01, 0x0F]), [Section(0x1, 2), Section(0xF00, 2)])]
)
def test_packet_decode(sections: List[Section], value: bytes, expected: List[Section]):
    assert Packet(sections).decode(value) == expected

    
@pytest.mark.parametrize(
    "sections,value,expected", [([Section.Template(2), Section.Template(1)], bytes(
        [0x0, 0x01, 0x0F]), [Section(0x1, 2), Section(0xF, 1)]), ([Section.Template(2), Section.Template(2)], bytes(
        [0x0, 0x01, 0x0F]), [Section(0x0, 2), Section(0x10F, 2)])]
)
def test_packet_decode_leading_bytes(sections: List[Section], value: bytes, expected: List[Section]):
    assert Packet(sections).decode(value, Zeros.LEADING) == expected

