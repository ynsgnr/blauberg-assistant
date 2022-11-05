from typing import List
from math import floor

byte_size_error = ValueError("byte_size can not be less than zero")
value_fit_error = OverflowError("value does not fit into the byte size")

class Section:
    """Represents a section of a packet"""

    __slots__ = ['value', 'byte_size']

    def __init__(self,  value:int = 0, byte_size:int = 0):
        value_size = floor(value.bit_length()/8) + 1
        if byte_size==0:
            byte_size = value_size
        if byte_size<0:
            raise byte_size_error
        if value_size>byte_size:
            raise value_fit_error
        self.value = value
        self.byte_size = byte_size

    def to_bytes(self) -> bytes:
        return self.value.to_bytes(self.byte_size, byteorder='big')
    
    def __str__(self) -> str:
        # each byte has two chars in hex reporesantation
        return "0x{0:0{1}X}".format(self.value,self.byte_size*2)
        
    def __repr__(self) -> str:
        return self.__str__()

class Packet(List[Section]):
    """Represents a packet as a list of sections, it extends on list itself so all methods for lists can be used"""

    def to_int(self) -> int:
        return int.from_bytes(self.to_bytes(), "big")

    def to_bytes(self) -> bytes:
        result = bytearray()
        for section in self:
            result.extend(section.to_bytes())
        return bytes(result)

    def byte_size(self) -> int:
        return sum(section.byte_size for section in self)
    
    def __str__(self) -> str:
        # each byte has two chars in hex reporesantation
        return "0x{0:0{1}X}".format(self.to_int(),self.byte_size()*2)