from .section import Section
from .zeros import Zeros
from typing import Any
from .errors import byte_size_error, value_overflow_error


class DynamicSection(Section):
    """Represents a section that changes size according to the first byte of decoding value
        the first byte is called length byte because it determines the length of bytes that needs
        to be read and set as value. The length byte's size can be set with length_byte_size
        set_bytes for this class only sets the value without the size byte so input should not include size byte
    """

    __slots__ = ['length_byte_size']

    def __init__(self, length_byte_size: int = 1,  trail_or_lead: Zeros = Zeros.LEADING):
        if length_byte_size <= 0:
            raise byte_size_error
        super().__init__(0, 0, trail_or_lead)
        self.length_byte_size = length_byte_size

    """sets the value and the byte size according to value size for the section from given bytes, input shouldn't include length bytes
        if length of value doesn't fit into the length byte size which is set during initialization (length_byte_size), it raises overflow error
    """

    def set_bytes(self, bytes_value: bytes) -> Section:
        self.byte_size = len(bytes_value)
        if self._minimum_byte_size(self.byte_size) > self.length_byte_size:
            raise value_overflow_error
        super().set_bytes(bytes_value)
        return self

    """returns length of value as bytes and value as bytes appended, if needed inserts zeros according the initialized leading or trailing zeros config
        length bytes are always the first byte independent of the trailing or leading zeros config
    """

    def to_bytes(self) -> bytes:
        return Section(value=self.byte_size, byte_size=self.length_byte_size).to_bytes() + super().to_bytes()

    """decodes given bytes into byte size and value, start from left most
        first n bytes determines the byte size, n being the length byte size which is set during initialization (length_byte_size)
        the value in the first n bytes determines the byte size which determines how many bytes to be read and saved as section value
        the remaining bytes after byte size is read are returned
    """

    def partial_decode(self, bytes_value: bytes) -> bytes:
        length_section = Section.Template(self.length_byte_size)
        bytes_value = length_section.partial_decode(bytes_value)
        self.byte_size = length_section.value
        return super().partial_decode(bytes_value)

    def __str__(self) -> str:
        # each byte has two chars in hex representation
        return "0x{0:0{1}X} - 0x{0:0{1}X}".format(self.byte_size, self.length_byte_size, self.value, self.byte_size*2)

    def __eq__(self, other: Any):
        return isinstance(other, self.__class__) and self.value == other.value and self.byte_size == other.byte_size and self.length_byte_size == other.length_byte_size

    def __hash__(self) -> int:
        return hash((self.value, self.byte_size, self.length_byte_size))
