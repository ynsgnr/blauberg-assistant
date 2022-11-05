from typing import List
from math import floor, log, ceil

byte_size_error = ValueError("byte_size can not be less than zero")
value_fit_error = ValueError("value does not fit into the byte size")

class Section:
    """Represents a section of a packet"""

    __slots__ = ['value', 'byte_size']
    
    def _minDigit(self, n:int, base:int=16) -> int:
        if n == 0:
            return 1
        if n == 1:
            return 1
        return floor(log(abs(n))/log(base)+1)

    def __init__(self,  value:int = 0, byte_size:int = 0):
        minumum_byte_size = ceil(self._minDigit(value)/2)
        if byte_size==0:
            byte_size = minumum_byte_size
        if byte_size<0:
            raise byte_size_error
        if minumum_byte_size>byte_size:
            raise value_fit_error
        self.value = value
        self.byte_size = byte_size
    
    def __str__(self) -> str:
        # each byte has two chars in hex reporesantation
        return "0x{0:0{1}X}".format(self.value,self.byte_size*2)
        
    def __repr__(self) -> str:
        return self.__str__()

class Packet(List[Section]):
    """Represents a packet as a list of sections, it extends on list itself so all methods for lists can be used"""

    def build(self) -> int:
        packet:int = 0
        for section in self:
            packet = packet << section.byte_size*8 | section.value
        return packet

    def byte_size(self) -> int:
        return sum(section.byte_size for section in self)
    
    def __str__(self) -> str:
        # each byte has two chars in hex reporesantation
        return "0x{0:0{1}X}".format(self.build(),self.byte_size()*2)