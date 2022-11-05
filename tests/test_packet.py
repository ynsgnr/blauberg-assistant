
import pytest
from custom_components.blaueberg.packet import *

@pytest.mark.parametrize(
    "n,expected", [(0x0, 1), (0x1, 1), (0x2, 1), (0x10, 2), (0x11, 2), (0xFF, 2), (0x00FF, 2)]
)
def test_section_minDigit_hex(n:int, expected:int):
    assert Section()._minDigit(n) == expected # type: ignore

    
@pytest.mark.parametrize(
    "n,expected", [(0, 1), (1, 1), (2, 1), (10, 2), (11, 2), (1111, 4)]
)
def test_section_minDigit_decimal(n:int, expected:int):
    assert Section()._minDigit(n,10) == expected # type: ignore

    
@pytest.mark.parametrize(
    "value,byte_size,exception", [(0, -1, ValueError("byte_size can not be less than zero")), (0x111, 1, ValueError("value does not fit into the byte size"))]
)
def test_section_init_with_exception(value:int,byte_size:int,exception:Exception):
    with pytest.raises(type(exception)) as exc_info:
        Section(value, byte_size)
    assert str(exception) == str(exc_info.value)

@pytest.mark.parametrize(
    "value,byte_size", [(0, 0), (0, 1), (0x11, 1), (0x1FFF,2)]
)
def test_section_init(value:int,byte_size:int):
    Section(value, byte_size)

@pytest.mark.parametrize(
    "sections,expected", [([Section(0x1,2),Section(0xF,1)],0x010F),([Section(0x1,1),Section(0x1FFF,2)],0x011FFF)]
)
def test_packet_build(sections:List[Section], expected:int):
    assert Packet(sections).build() == expected