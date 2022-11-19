from __future__ import annotations
from typing import Union
from enum import Enum
from .errors import value_overflow_error


class Zeros(Enum):
    TRAILING = 1
    LEADING = 2

    @staticmethod
    def insert(zeros: Zeros, data: Union[bytes, bytearray], byte_size: int) -> bytes:
        value = bytes(data)
        if len(data) > byte_size:
            raise value_overflow_error
        diff = byte_size - len(value)
        if zeros == Zeros.TRAILING:
            value = value + bytes([0 for _ in range(diff)])
        else:
            value = bytes([0 for _ in range(diff)]) + value
        return value
