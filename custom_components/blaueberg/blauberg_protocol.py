
from __future__ import annotations
from typing import Optional
from .packet import Packet, Section, ExpandingSection
import socket
import copy

import logging
LOG = logging.getLogger(__name__)

BUFFER_SIZE = 4096


class BlaubergProtocol():
    """Utility class to communicate with blauberg wifi protocol for their fans"""

    HEADER = Section(0xFDFD)
    PROTOCOL_TYPE = Section(0x02)
    ID_SIZE = Section(0x10)
    PWD_SIZE = Section(0x04)
    CHECKSUM = Section.Template(2)
    LEAD_INDICATOR = Section(0xFF)
    INVALID = Section(0xFD)
    DYNAMIC_VAL = Section(0xFE)
    BLANK_BYTE = ExpandingSection()

    class FUNC:
        Template = Section.Template(1)
        R = Section(0x01)
        RW = Section(0x03)

    PROTOCOL = [HEADER, PROTOCOL_TYPE, ID_SIZE, Section.Template(ID_SIZE.value), PWD_SIZE, Section.Template(
        PWD_SIZE.value), FUNC.Template, ExpandingSection(), CHECKSUM]

    RESPONSE = [HEADER, PROTOCOL_TYPE, ID_SIZE, Section.Template(
        ID_SIZE.value), PWD_SIZE, FUNC.Template, ExpandingSection(), CHECKSUM]

    def __init__(self,
                 host: str,
                 port: int = 4000,
                 password: str = "1111",
                 device_id: str = "DEFAULT_DEVICEID"):
        self._host = host
        self._port = port
        self._password = password
        self._device_id = device_id

    def _protocol(self) -> Packet:
        return Packet(copy.deepcopy(self.PROTOCOL))

    def _response(self) -> Packet:
        return Packet(copy.deepcopy(self.RESPONSE))

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

    @staticmethod
    def _swap_high_low(value: int, swap_size: int = 8) -> int:
        return (value << swap_size & int('1'*swap_size+'0'*swap_size, 2) | value >> swap_size & int('0'*swap_size+'1'*swap_size, 2))

    def _checksum(self, data: Packet) -> Section:
        check_sum = sum(data.to_bytes())
        return Section(self._swap_high_low(check_sum), 2)

    def _command(self, function: Section, data: Packet) -> Packet:
        command = self._protocol()
        command[3].set_bytes(bytes(self._device_id, 'utf-8'))
        command[5].set_bytes(bytes(self._password, 'utf-8'))
        command[6] = function
        command[7] = Section(data.to_int(), data.byte_size())
        command[8] = self._checksum(Packet(command[1:-1]))
        return command

    def _communicate_block(self, function: Section, data: Packet) -> Section:
        LOG.info("constructing command from data packet:" + str(data))
        command = self._command(function, data)
        LOG.info("sending command:" + str(command))
        raw_response = self._communicate(command.to_bytes())
        LOG.info("received raw response:" + str(raw_response))
        if len(raw_response) == 0:
            return self.BLANK_BYTE

        # Exclude checksum due to data section being expandible
        response = self._response().decode(raw_response[:-2])
        LOG.info("parsed raw response:" + str(response))

        actual_check_sum = self.CHECKSUM.set_bytes(raw_response[-2:]).value
        expected_check_sum = self._checksum(Packet(response[1:-1])).value
        if actual_check_sum != expected_check_sum:
            LOG.warn("invalid checksum response: expected: " +
                     str(expected_check_sum) + " actual: " + str(actual_check_sum))

        return response[-2]

    def _decode_data(self, raw_data: bytes) -> dict[int, Optional[int]]:
        values: dict[int, Optional[int]] = {}
        lead_byte = bytes()
        index = 0
        while index < len(raw_data):
            func = raw_data[index]
            if func == self.LEAD_INDICATOR.value:
                index += 1
                lead_byte = bytes([raw_data[index]])
                index += 1
            elif func == self.INVALID.value:
                index += 1
                tail_byte = bytes([raw_data[index]])
                index += 1
                param = Section.Template(2).set_bytes(
                    lead_byte+tail_byte).value
                if param not in values:
                    values[param] = None
            elif func == self.DYNAMIC_VAL.value:
                index += 1
                byte_length = raw_data[index]
                index += 1
                if (index+byte_length) > len(raw_data):
                    LOG.warn(
                        "byte length given is bigger than length of remaining bytes")
                    return values
                tail_byte = bytes([raw_data[index]])
                index += 1
                param = Section.Template(2).set_bytes(
                    lead_byte+tail_byte).value
                dynamic_part = raw_data[index:(index+byte_length)]
                value = Section.Template(
                    byte_length).set_bytes(dynamic_part).value
                values[param] = value
                index += byte_length
            else:
                tail_byte = bytes([raw_data[index]])
                index += 1
                param = Section.Template(2).set_bytes(
                    lead_byte+tail_byte).value
                value = raw_data[index]
                index += 1
                values[param] = value
        return values

    def _construct_read_command_block(self, parameters: list[int]) -> Packet:
        parameters.sort()
        params_by_lead: dict[int, list[int]] = {}
        for param in parameters:
            raw = Section(param, 2).to_bytes()
            lead = raw[0]
            tail = raw[1]
            if lead not in params_by_lead:
                params_by_lead[lead] = []
            params_by_lead[lead].append(tail)

        data_packet = Packet()
        for lead in params_by_lead:
            data_packet.append(self.LEAD_INDICATOR)
            data_packet.append(Section(lead))
            for tail in params_by_lead[lead]:
                data_packet.append(Section(tail))
        return data_packet

    def _read_params(self, parameters: list[int]) -> dict[int, Optional[int]]:
        data_response = self._communicate_block(
            self.FUNC.R, self._construct_read_command_block(parameters))
        raw_data = data_response.to_bytes()
        return self._decode_data(raw_data)

    def read_param(self, param: int) -> int:
        params = self._read_params([param])
        if param not in params:
            return 0
        return params[param] or 0

    def write_param(self, parameter: int, value: int) -> dict[int, Optional[int]]:
        data_response = self._communicate_block(
            self.FUNC.RW, Packet([Section(parameter), Section(value)]))
        raw_data = data_response.to_bytes()
        return self._decode_data(raw_data)

    def turn_on(self):
        self.write_param(0x01, 0x01)

    def turn_off(self):
        self.write_param(0x01, 0x00)

    def fan_speed(self) -> int:
        return self.read_param(0x04)

    def moisture(self) -> int:
        return self.read_param(0x2e)

    def temperature(self) -> int:
        return self.read_param(0x31)
