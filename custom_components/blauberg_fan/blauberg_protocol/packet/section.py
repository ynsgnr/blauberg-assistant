from __future__ import annotations
from typing import Any
from math import ceil
from .zeros import Zeros
from .errors import byte_size_error, value_overflow_error


class Section:
    """Represents a section of a packet"""

    __slots__ = ["value", "byte_size", "trail_or_lead"]

    @staticmethod
    def Template(byte_size: int, trail_or_lead: Zeros = Zeros.LEADING) -> Section:
        return Section(0, byte_size, trail_or_lead)

    @staticmethod
    def _minimum_byte_size(value: int) -> int:
        size = ceil(value.bit_length() / 8)
        if size == 0:
            return 1
        return size

    def __init__(
        self, value: int = 0, byte_size: int = 0, trail_or_lead: Zeros = Zeros.LEADING
    ) -> None:
        value_size = self._minimum_byte_size(value)
        if byte_size == 0:
            byte_size = value_size
        if byte_size < 0:
            raise byte_size_error
        if value_size > byte_size:
            raise value_overflow_error
        self.value = value
        self.byte_size = byte_size
        self.trail_or_lead = trail_or_lead

    def to_bytes(self) -> bytes:
        """returns value as bytes, if needed inserts zeros according the initialized leading or trailing zeros config"""
        return Zeros.insert(
            self.trail_or_lead,
            self.value.to_bytes(self.byte_size, byteorder="big"),
            self.byte_size,
        )

    def set_bytes(self, bytes_value: bytes) -> Section:
        """sets only the value for the section from given bytes"""
        value = Zeros.insert(self.trail_or_lead, bytes_value, self.byte_size)
        new_value = int.from_bytes(value, "big")
        new_value_size = self._minimum_byte_size(new_value)
        if (
            not (self.byte_size == 0 and new_value == 0)
            and new_value_size > self.byte_size
        ):
            raise value_overflow_error
        self.value = new_value
        return self

    def partial_decode(self, bytes_value: bytes) -> bytes:
        """decodes only the relevant part of a given byte array and returns the remaining bytes, starts from leftmost byte"""
        max_len = len(bytes_value)
        if self.byte_size < max_len:
            max_len = self.byte_size
        self.set_bytes(bytes_value[0:max_len])
        return bytes_value[max_len:]

    def __str__(self) -> str:
        # each byte has two chars in hex representation
        return "0x{0:0{1}X}".format(self.value, self.byte_size * 2)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: Any):
        return (
            isinstance(other, self.__class__)
            and self.value == other.value
            and self.byte_size == other.byte_size
        )

    def __hash__(self) -> int:
        return hash((self.value, self.byte_size))
