from .section import Section


class ExpandingSection(Section):
    """Represents a section that expands while decoding or setting bytes"""

    def __init__(self):
        super().__init__()

    """sets the value and the byte size according to values max size"""

    def set_bytes(self, bytes_value: bytes) -> Section:
        self.byte_size = len(bytes_value)
        super().set_bytes(bytes_value)
        return self

    """decodes all of the given bytes and set it as value while updating its own byte size. Returns empty list"""

    def partial_decode(self, bytes_value: bytes) -> bytes:
        self.set_bytes(bytes_value)
        return bytes()
