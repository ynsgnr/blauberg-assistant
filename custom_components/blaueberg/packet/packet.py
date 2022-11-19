from __future__ import annotations
from typing import List, Union
from .section import Section
from .zeros import Zeros
from .errors import value_overflow_error

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

    def decode(self, bytes_value: Union[bytes, bytearray], zeros: Zeros = Zeros.TRAILING) -> Packet:
        value = bytes(bytes_value)
        byte_size = self.byte_size()
        if len(value)>byte_size:
            raise value_overflow_error
        diff = byte_size - len(value)
        if zeros == Zeros.TRAILING:
            value = value + bytes([0 for _ in range(diff)])
        else:
            value = bytes([0 for _ in range(diff)]) + value
        index = 0
        for section in self:
            new_index = index+section.byte_size
            section.set_bytes(value[index:new_index])
            index = new_index
        return self

    def __str__(self) -> str:
        # each byte has two chars in hex representation
        return "0x{0:0{1}X}".format(self.to_int(), self.byte_size()*2)
