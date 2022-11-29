
import pytest
from custom_components.blauberg_fan.packet.packet import *
from custom_components.blauberg_fan.packet.expanding_section import *
from custom_components.blauberg_fan.packet.dynamic_section import *
from custom_components.blauberg_fan.packet.errors import *


@pytest.mark.parametrize(
    "sections,expected", [
        ([Section(0x1, 2), Section(0xF)], 0x010F),
        ([Section(0x1), Section(0x1FFF, 2)], 0x011FFF)
    ]
)
def test_packet_to_int(sections: List[Section], expected: int):
    assert Packet(sections).to_int() == expected


@pytest.mark.parametrize(
    "sections,expected", [
        ([Section(0x1, 2), Section(0xF)], bytes([0x0, 0x01, 0x0F])),
        ([Section(0x1), Section(0x1FFF, 2)], bytes([0x01, 0x1F, 0xFF]))
    ]
)
def test_packet_to_bytes(sections: List[Section], expected: int):
    assert Packet(sections).to_bytes() == expected


@pytest.mark.parametrize(
    "sections,value,expected", [
        ([Section.Template(2), Section.Template(1)], bytes(
            [0x0, 0x01, 0x0F]), [Section(0x1, 2), Section(0xF, 1)]),
        ([Section.Template(2), Section.Template(2)], bytes(
            [0x0, 0x01, 0x0F]), [Section(0x1, 2), Section(0xF00, 2)])
    ]
)
def test_packet_decode(sections: List[Section], value: bytes, expected: List[Section]):
    assert Packet(sections).decode(value) == expected


@pytest.mark.parametrize(
    "sections,value,expected", [
        ([Section.Template(2), Section.Template(1), ExpandingSection()], bytes([0x0, 0x01, 0x0F, 0x02]),  [
         Section(0x1, 2), Section(0xF, 1), ExpandingSection().set_bytes(bytes([0x02]))]),
        ([Section.Template(1), ExpandingSection()], bytes([0x01, 0x01, 0x0F, 0x03]),  [
         Section(0x1, 1), ExpandingSection().set_bytes(bytes([0x01, 0x0F, 0x03]))]),
        ([Section.Template(1), ExpandingSection(), Section.Template(1)], bytes([0x01, 0x01, 0x0F, 0x03]),  [
         Section(0x1, 1), ExpandingSection().set_bytes(bytes([0x01, 0x0F, 0x03])), Section()])
    ]
)
def test_packet_decode_with_expanding_section(sections: List[Section], value: bytes, expected: List[Section]):
    assert Packet(sections).decode(value) == expected


@pytest.mark.parametrize(
    "sections,value,expected", [
        ([Section.Template(2), DynamicSection()], bytes([0x0, 0x01, 0x01, 0x02]),  [
         Section(0x1, 2), DynamicSection().set_bytes(bytes([0x02]))]),
        ([Section.Template(2), DynamicSection(), Section.Template(1), ], bytes([0x0, 0x01, 0x02, 0x02,
         0x03, 0x04]),  [Section(0x1, 2), DynamicSection().set_bytes(bytes([0x02, 0x03])), Section(0x4)]),
        ([DynamicSection(), Section.Template(1)], bytes([0x03, 0x01, 0x02]),
         [DynamicSection().set_bytes(bytes([0x01, 0x02, 0x0])), Section()])
    ]
)
def test_packet_decode_with_dynamic_section(sections: List[Section], value: bytes, expected: List[Section]):
    assert Packet(sections).decode(value) == expected


@pytest.mark.parametrize(
    "sections,value,expected", [
        ([Section.Template(2), DynamicSection(), ExpandingSection()], bytes([0x0, 0x01, 0x02, 0x0A, 0x0B, 0x0F, 0x02]),  [
         Section(0x1, 2), DynamicSection().set_bytes(bytes([0x0A, 0x0B])), ExpandingSection().set_bytes(bytes([0x0F, 0x02]))]),
        ([Section.Template(1), ExpandingSection(), DynamicSection()], bytes([0x01, 0x01, 0x0F, 0x03]),  [
         Section(0x1, 1), ExpandingSection().set_bytes(bytes([0x01, 0x0F, 0x03])), DynamicSection()])
    ]
)
def test_packet_decode_with_dynamic_and_expanding_section(sections: List[Section], value: bytes, expected: List[Section]):
    assert Packet(sections).decode(value) == expected


@pytest.mark.parametrize(
    "sections,value,expected", [
        ([Section.Template(2), Section.Template(1)], bytes(
            [0x0, 0x01, 0x0F]), [Section(0x1, 2), Section(0xF, 1)]),
        ([Section.Template(2), Section.Template(2)], bytes(
            [0x0, 0x01, 0x0F]), [Section(0x0, 2), Section(0x10F, 2)])
    ]
)
def test_packet_decode_leading_bytes(sections: List[Section], value: bytes, expected: List[Section]):
    assert Packet(sections).decode(value, Zeros.LEADING) == expected
