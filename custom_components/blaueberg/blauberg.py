
from __future__ import annotations
from .packet import Packet, Section
import socket
import logging
import copy

LOG = logging.getLogger(__name__)

BUFFER_SIZE = 4096


class Blauberg():
    """Utility class to communicate with blauberg wifi protocol for their fans"""

    HEADER = Section(0xFDFD)
    PROTOCOL_TYPE = Section(0x02)
    ID_SIZE = Section(0x10)
    PWD_SIZE = Section(0x04)
    CHECKSUM = Section.Template(2)

    class FUNC:
        Template = Section.Template(1)
        R = Section(0x01)
        RW = Section(0x03)

    PROTOCOL = [HEADER, PROTOCOL_TYPE, ID_SIZE, Section.Template(ID_SIZE.value), PWD_SIZE, Section.Template(
        PWD_SIZE.value), FUNC.Template, Section.Template(4), CHECKSUM]

    def __init__(self,
                 host: str,
                 port: int = 4000,
                 password: str = "1111",
                 device_id: str = "DEFAULT_DEVICEID"):
        self._host = host
        self._port = port
        self._password = password
        self._device_id = device_id
        self._id = id

    def _connect(self) -> socket.socket:
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.settimeout(4)
        conn.connect((self._host, self._port))
        return conn

    def _communicate(self, data: bytes) -> bytes:
        conn = self._connect()
        conn.sendall(data)
        response = bytes()
        try:
            response = conn.recv(BUFFER_SIZE)
        except socket.timeout:
            LOG.error("timeout")
        conn.close()
        return response

    def _checksum(self, data: Packet) -> Section:
        int_sum = sum(Packet(data[1:8]).to_bytes())
        #  Switch high and low bytes
        switched_sum = (int_sum << 8 | int_sum >> 8) & 0xFFFF
        return Section(switched_sum, 2)

    def _command(self, function: Section, data: Packet) -> Packet:
        command = Packet(copy.deepcopy(self.PROTOCOL))
        command[3].set_value(bytes(self._device_id, 'utf-8'))
        command[5].set_value(bytes(self._password, 'utf-8'))
        command[6] = function
        command[7] = Section(data.to_int(), data.byte_size())
        command[8] = self._checksum(command)
        return command

    def _write(self, parameter: Section, value: Section) -> bytes:
        command = self._command(self.FUNC.RW, Packet(
            [parameter, value]))
        return self._communicate(command.to_bytes())

        
    def _read(self, parameter: Section) -> bytes:
        command = self._command(self.FUNC.R, Packet(
            [parameter]))
        return self._communicate(command.to_bytes())

    def turn_on(self):
        self._write(Section(0x01),Section(0x01))
        
    def turn_off(self):
        self._write(Section(0x01),Section(0x00))
