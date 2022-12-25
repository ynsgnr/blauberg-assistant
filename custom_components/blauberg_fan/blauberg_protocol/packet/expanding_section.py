from .section import Section
from .zeros import Zeros


class ExpandingSection(Section):
    """Represents a section that expands while decoding or setting bytes"""

    def __init__(self):
        self.value = 0
        self.byte_size = 0
        self.trail_or_lead = Zeros.LEADING

    def set_bytes(self, bytes_value: bytes) -> Section:
        """sets the value and the byte size according to values max size"""
        self.byte_size = len(bytes_value)
        super().set_bytes(bytes_value)
        return self

    def partial_decode(self, bytes_value: bytes) -> bytes:
        """decodes all of the given bytes and set it as value while updating its own byte size. Returns empty list"""
        self.set_bytes(bytes_value)
        return bytes()
