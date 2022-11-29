
import pytest
from custom_components.blauberg_fan.packet import *
from custom_components.blauberg_fan.packet.errors import *


@pytest.mark.parametrize(
    "zeros,data,byte_size,expected", [
        (Zeros.TRAILING, bytes([0xFF]), 1,  bytes([0xFF])),
        (Zeros.LEADING, bytes([0xFF]), 1,  bytes([0xFF])),
        (Zeros.TRAILING, bytes([0xFF]), 2,  bytes([0xFF, 0x00])),
        (Zeros.LEADING, bytes([0xFF]), 2,  bytes([0x00, 0xFF]))
    ]
)
def test_zeros_insert(zeros: Zeros, data: bytes, byte_size: int, expected: int):
    assert Zeros.insert(zeros, data, byte_size) == expected


@pytest.mark.parametrize(
    "zeros,data,byte_size,exception", [
        (Zeros.TRAILING, bytes([0xFF, 0xFF]), 1, value_overflow_error),
        (Zeros.LEADING, bytes([0xFF, 0xFF]), 1, value_overflow_error)]
)
def test_zeros_insert_with_exception(zeros: Zeros, data: bytes, byte_size: int, exception: Exception):
    with pytest.raises(type(exception)) as exc_info:
        Zeros.insert(zeros, data, byte_size)
    assert str(exception) == str(exc_info.value)
