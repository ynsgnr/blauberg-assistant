from __future__ import annotations
from typing import List, Union
from .section import Section
from .zeros import Zeros


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

    def decode(self, bytes_value: Union[bytes, bytearray], trail_or_lead: Zeros = Zeros.TRAILING) -> Packet:
        value = Zeros.insert(trail_or_lead, bytes_value, self.byte_size())
        for section in self:
            value = section.partial_decode(value)
        return self

    def __str__(self) -> str:
        # each byte has two chars in hex representation
        return "0x{0:0{1}X}".format(self.to_int(), self.byte_size()*2)
