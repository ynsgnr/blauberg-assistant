
import pytest
from custom_components.blaueberg.packet.packet import *
from custom_components.blaueberg.packet.errors import *


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


@pytest.mark.parametrize(
    "sections,value,exception", [
        ([Section.Template(1), Section.Template(1)], bytes(
            [0x0, 0x01, 0x0F]), value_overflow_error)]
)
def test_packet_decode_with_exception(sections: List[Section], value: bytes, exception: Exception):
    with pytest.raises(type(exception)) as exc_info:
        Packet(sections).decode(value)
    assert str(exception) == str(exc_info.value)
