
import pytest
from custom_components.blaueberg.packet import *

    
@pytest.mark.parametrize(
    "value,byte_size,exception", [(0, -1, ValueError("byte_size can not be less than zero")), (0x111, 1, OverflowError("value does not fit into the byte size"))]
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
    "value,byte_size,expected", [(0, 0, bytes([0])), (0, 1, bytes([0])), (0x11, 1, bytes([0x11])), (0x1FFF,2, bytes([0x1F,0xFF])), (0x1FFF,3, bytes([0x0, 0x1F,0xFF]))]
)
def test_section_to_bytes(value:int,byte_size:int, expected:bytes):
    assert Section(value, byte_size).to_bytes() == expected

@pytest.mark.parametrize(
    "sections,expected", [([Section(0x1,2),Section(0xF)],0x010F),([Section(0x1),Section(0x1FFF,2)],0x011FFF)]
)
def test_packet_to_int(sections:List[Section], expected:int):
    assert Packet(sections).to_int() == expected

    
@pytest.mark.parametrize(
    "sections,expected", [([Section(0x1,2),Section(0xF)],bytes([0x0,0x01,0x0F])),([Section(0x1),Section(0x1FFF,2)],bytes([0x01,0x1F,0xFF]))]
)
def test_packet_to_bytes(sections:List[Section], expected:int):
    assert Packet(sections).to_bytes() == expected