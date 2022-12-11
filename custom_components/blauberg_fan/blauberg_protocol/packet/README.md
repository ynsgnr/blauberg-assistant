# Packet
A byte manipulation tool for IoT and network communications.

This module aims to simplify writing protocols for I/O by allowing declarative byte parsing.

## Usage
Since this module is not published yet it only works with relative import, so python console needs to run on the same level as this module's folder
```python
from .packet import Packet, Section

packet = Packet([Section(0x1100),Section(value=0x11,byte_size=2)])
packet.to_bytes() # 0x11000011

response =  Packet([Section.Template(2),Section.Template(byte_size=3)])
raw_data = bytes([1,2,3,4,5])
response.decode(raw_data)
response[0] # 0x0102
response[-1] # 0x030405
```

## Features
- Simple and familiar API:
  - Each Section has two parameters: value and byte size.
  - Packet object is just a section array with `to_bytes`, `to_int` and `decode` functions added, which means its easier to read
  - `Section.Template` makes easier to read without adding extra complexity. This function just sets the `byte_size` and returns a regular Section for its value to be filled during parsing
- Expandable
  - Sections can parse data as long as they desire, so they are not limited with their byte size. This allows expanded section implementations
- Fast
  - Packet is making use of integer and byte shifting logic with some loops, so no string parsing and decoding going on speeding up the process
- Supports trailing or leading zeros! `Packet(trail_or_lead=Zeros.LEADING)` or `Section(trail_or_lead=Zeros.LEADING)`

## Sections
### Section
Simple section with a value and byte size. Used for sections in byte array protocols with fixed length
### Expanding Section
When this section is added to packet, it consumes all remaining bytes and sets its own length. Used for sections that require custom parsing with custom logic, returned value can be parsed manually after parsing
### Dynamic Section
This section sets its own first byte as the length byte. Used for transmitting and decoding protocols with flexible lengths