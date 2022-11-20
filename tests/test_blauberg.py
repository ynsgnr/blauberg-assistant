
from __future__ import annotations
import pytest
from custom_components.blaueberg.blauberg import *

TEST_HOST = "0.0.0.0"


@pytest.mark.parametrize(
    "input,expected", [(0xFFDD, 0xDDFF), (0x0102, 0x0201),
                       (0x55443322, 0x2233)]
)
def test_blauberg_swap_high_low(input: int, expected: int):
    assert Blauberg(host=TEST_HOST)._swap_high_low(  # type: ignore
        input) == expected


@pytest.mark.parametrize(
    "input,swap_size,expected", [
        (0xFFDD, 4, 0xDD), (0x55443322, 16, 0x33225544)]
)
def test_blauberg_swap_high_low_with_size(input: int, swap_size: int, expected: int):
    assert Blauberg(host=TEST_HOST)._swap_high_low(  # type: ignore
        input, swap_size) == expected


@pytest.mark.parametrize(
    "input,expected", [([0x9B, 0x70, 0x07], Packet([Section(0xFF), Section(0x00), Section(0x07), Section(0x70), Section(0x9B)])), ([0x109B, 0x1070, 0x2007, 0x2008, 0x09], Packet(
        [Section(0xFF), Section(0x00), Section(0x09), Section(0xFF), Section(0x10), Section(0x70), Section(0x9B), Section(0xFF), Section(0x20), Section(0x07), Section(0x08)]))]
)
def test_blauberg_construct_read_command_block(input: list[int], expected: Packet):
    assert Blauberg(host=TEST_HOST)._construct_read_command_block(  # type: ignore
        input) == expected


@pytest.mark.parametrize(
    "input,expected", [(bytes([0x9B, 0x02, 0x07, 0x01]), {0x9B: 0x02, 0x07: 0x01}),
                       (bytes([0xFD, 0x01]), {0x01: None}),
                       (bytes([0xFD, 0x01, 0x9B, 0x02]), {0x01: None, 0x9B: 0x02}),
                       (bytes([0xFE, 0x04, 0x70, 0x04, 0x85, 0x37, 0x42]), {
                        0x70: 0x42378504}),
                       (bytes([0x9B, 0x02, 0xFE, 0x04, 0x70, 0x04, 0x85, 0x37, 0x42, 0x07, 0x01]), {
                        0x9B: 0x02, 0x70: 0x42378504, 0x07: 0x01}),
                       (bytes([0xFF, 0x01, 0xFD, 0x01, 0x04, 0x05, 0xFF, 0x02, 0xFE, 0x02, 0x40, 0x51, 0x68]), {0x0101: None, 0x0104: 0x05, 0x0240: 0x6851})]
)
def test_blauberg_decode_data(input: bytes, expected: dict[int, Optional[int]]):
    assert Blauberg(host=TEST_HOST)._decode_data(  # type: ignore
        input) == expected