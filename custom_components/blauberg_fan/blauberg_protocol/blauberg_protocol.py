from __future__ import annotations
from collections.abc import Mapping
from ezpacket import Packet, Section, ExpandingSection, DynamicSection
import socket
import ifaddr
from ipaddress import IPv4Network

import logging

LOG = logging.getLogger(__name__)

BUFFER_SIZE = 4096


class BlaubergProtocol:
    """Utility class to communicate with blauberg wifi protocol for their fans"""

    HEADER = Section(0xFDFD)
    PROTOCOL_TYPE = Section(0x02)
    CHECKSUM = Section.Template(2)
    LEAD_INDICATOR = Section(0xFF)
    INVALID = Section(0xFD)
    DYNAMIC_VAL = Section(0xFE)
    BLANK_BYTE = ExpandingSection()

    DEFAULT_PORT = 4000
    DEFAULT_TIMEOUT = 1
    DEFAULT_PWD = "1111"
    DEFAULT_DEVICE_ID = "DEFAULT_DEVICEID"

    class FUNC:
        Template = Section.Template(1)
        R = Section(0x01)
        RW = Section(0x03)

    @staticmethod
    def _broadcast_addresses() -> list[str]:
        nets = []
        adapters = ifaddr.get_adapters()
        for adapter in adapters:
            for ip in adapter.ips:
                if ip.is_IPv4 and ip.network_prefix < 32:
                    localNet = IPv4Network(f"{ip.ip}/{ip.network_prefix}", strict=False)
                    if (
                        localNet.is_private
                        and not localNet.is_loopback
                        and not localNet.is_link_local
                    ):
                        nets.append(str(localNet.broadcast_address))
        return nets

    @staticmethod
    def _broadcast(port: int, timeout: float, data: bytes) -> list[tuple[bytes, str]]:
        destinations = BlaubergProtocol._broadcast_addresses()
        LOG.debug(
            "broadcasting: %s to: %s with port: %s",
            str(data),
            str(destinations),
            str(port),
        )
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(timeout)
        for dest in destinations:
            s.sendto(data, (dest, port))
        responses = []
        timeout = False
        while not timeout:
            try:
                responses.append(s.recvfrom(BUFFER_SIZE))
            except socket.timeout:
                timeout = True
        LOG.debug("responses: %s", str(responses))
        return responses

    @staticmethod
    def discover_device(
        host: str,
        port: int = DEFAULT_PORT,
        password: str = DEFAULT_PWD,
        timeout: float = DEFAULT_TIMEOUT,
        device_id_param: int = 0x7C,
    ) -> BlaubergProtocol | None:
        temp_protocol = BlaubergProtocol(
            host=host, port=port, timeout=timeout, password=""
        )
        # Complex blocks with lead indicator or dynamic values are not supported in discovery mode on the device
        # hence we need to use a simpler command to get device id
        data_response = temp_protocol._communicate_block(
            temp_protocol.FUNC.R, Packet([Section(device_id_param)])
        )
        if data_response == temp_protocol.BLANK_BYTE:
            return None
        params = temp_protocol._decode_data(data_response.to_bytes())
        raw_device_id = params.get(device_id_param)
        if raw_device_id is None or raw_device_id == 0:
            return None
        device_id = Section(raw_device_id).to_bytes().decode()
        temp_protocol._device_id = device_id
        temp_protocol._password = password
        return temp_protocol

    @staticmethod
    def discover(
        port: int = DEFAULT_PORT,
        password: str = DEFAULT_PWD,
        timeout: float = DEFAULT_TIMEOUT,
        device_id_param: int = 0x7C,
    ) -> list[BlaubergProtocol]:
        temp_protocol = BlaubergProtocol("")
        # Complex blocks with lead indicator or dynamic values are not supported in discovery mode on the device
        # hence we need to use a simpler command to get device id
        discover_command = temp_protocol._construct_command(
            temp_protocol.FUNC.R, Packet([Section(device_id_param)])
        )
        responses = temp_protocol._broadcast(port, timeout, discover_command.to_bytes())
        discoverd = []
        for resp in responses:
            (raw_response, (host, _)) = resp
            LOG.debug("received raw response: %s from %s", str(raw_response), host)
            if len(raw_response) != 0:
                # Exclude checksum due to data section being expandible
                response = temp_protocol._response().decode(raw_response[:-2])
                LOG.debug("parsed raw response: %s", str(response))

                actual_check_sum = temp_protocol.CHECKSUM.set_bytes(
                    raw_response[-2:]
                ).value
                expected_check_sum = temp_protocol._checksum(
                    Packet(response[1:-1])
                ).value
                if actual_check_sum == expected_check_sum:
                    data_block = response[-2]
                    params = temp_protocol._decode_data(data_block.to_bytes())
                    raw_device_id = params.get(device_id_param)
                    if raw_device_id is not None and raw_device_id != 0:
                        device_id = Section(raw_device_id).to_bytes().decode()
                        device = BlaubergProtocol(
                            host, port, device_id, password, timeout
                        )
                        if device.read_param(device_id_param) == raw_device_id:
                            discoverd.append(device)
                        else:
                            LOG.info(
                                "invalid device id response after discovery, check password"
                            )
                else:
                    LOG.info(
                        "invalid checksum response: expected: %s, actual: %s",
                        str(expected_check_sum),
                        str(actual_check_sum),
                    )
        return discoverd

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        device_id: str = DEFAULT_DEVICE_ID,
        password: str = DEFAULT_PWD,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if port <= 0:
            raise ValueError("port can not be less than or equal to zero")
        if device_id == "":
            raise ValueError("device id can not be blank")
        if timeout <= 0:
            raise ValueError("timeout can not be less than or equal to zero")
        self._host = host
        self._port = port
        self._device_id = device_id
        self._password = password
        self._timeout = timeout

    @property
    def device_id(self):
        return self._device_id

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def password(self):
        return self._password

    def _protocol(self) -> Packet:
        return Packet(
            [
                self.HEADER,
                self.PROTOCOL_TYPE,
                DynamicSection().set_bytes(bytes(self._device_id, "utf-8")),
                DynamicSection().set_bytes(bytes(self._password, "utf-8")),
                self.FUNC.Template,
                ExpandingSection(),
                self.CHECKSUM,
            ]
        )

    def _response(self) -> Packet:
        return Packet(
            [
                self.HEADER,
                self.PROTOCOL_TYPE,
                DynamicSection(),
                DynamicSection(),
                self.FUNC.Template,
                ExpandingSection(),
                self.CHECKSUM,
            ]
        )

    @staticmethod
    def _connect(host: str, port: int, timeout: float) -> socket.socket:
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.settimeout(timeout)
        conn.connect((host, port))
        return conn

    def _communicate(self, data: bytes) -> bytes:
        conn = self._connect(self._host, self._port, self._timeout)
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
        return value << swap_size & int(
            "1" * swap_size + "0" * swap_size, 2
        ) | value >> swap_size & int("0" * swap_size + "1" * swap_size, 2)

    @staticmethod
    def _checksum(data: Packet) -> Section:
        check_sum = sum(data.to_bytes())
        return Section(BlaubergProtocol._swap_high_low(check_sum), 2)

    def _construct_command(self, function: Section, data: Packet) -> Packet:
        LOG.debug(
            "constructing command from function: %s data packet: %s",
            str(function),
            str(data),
        )
        command = self._protocol()
        command[-3] = function
        command[-2] = Section(data.to_int(), data.byte_size())
        command[-1] = self._checksum(Packet(command[1:-1]))
        return command

    def _communicate_block(self, function: Section, data: Packet) -> Section:
        command = self._construct_command(function, data)

        LOG.debug("sending command: %s", str(command))
        raw_response = self._communicate(command.to_bytes())
        LOG.debug("received raw response: %s", str(raw_response))
        if len(raw_response) == 0:
            return self.BLANK_BYTE

        # Exclude checksum due to data section being expandible
        response = self._response().decode(raw_response[:-2])
        LOG.debug("parsed raw response: %s", str(response))

        actual_check_sum = self.CHECKSUM.set_bytes(raw_response[-2:]).value
        expected_check_sum = self._checksum(Packet(response[1:-1])).value
        if actual_check_sum != expected_check_sum:
            LOG.debug(
                "invalid checksum response: expected: %s actual: %s",
                str(expected_check_sum),
                str(actual_check_sum),
            )

        return response[-2]

    @staticmethod
    def _decode_data(raw_data: bytes) -> dict[int, int | None]:
        values: dict[int, int | None] = {}
        lead_byte = bytes()
        index = 0
        while index < len(raw_data):
            func = raw_data[index]
            if func == BlaubergProtocol.LEAD_INDICATOR.value:
                index += 1
                lead_byte = bytes([raw_data[index]])
                index += 1
            elif func == BlaubergProtocol.INVALID.value:
                index += 1
                tail_byte = bytes([raw_data[index]])
                index += 1
                param = Section.Template(2).set_bytes(lead_byte + tail_byte).value
                if param not in values:
                    values[param] = None
            elif func == BlaubergProtocol.DYNAMIC_VAL.value:
                index += 1
                byte_length = raw_data[index]
                index += 1
                if (index + byte_length) > len(raw_data):
                    LOG.debug(
                        "byte length given is bigger than length of remaining bytes"
                    )
                    return values
                tail_byte = bytes([raw_data[index]])
                index += 1
                param = Section.Template(2).set_bytes(lead_byte + tail_byte).value
                dynamic_part = raw_data[index : (index + byte_length)]
                value = Section.Template(byte_length).set_bytes(dynamic_part).value
                values[param] = value
                index += byte_length
            else:
                tail_byte = bytes([raw_data[index]])
                index += 1
                param = Section.Template(2).set_bytes(lead_byte + tail_byte).value
                value = raw_data[index]
                index += 1
                values[param] = value
        return values

    @staticmethod
    def _construct_command_block(parameters: Mapping[int, int | None]) -> Packet:
        params = list(parameters.keys())
        params.sort()
        params_by_lead: dict[int, list[int]] = {}
        for param in params:
            raw = Section(param, 2).to_bytes()
            lead = raw[0]
            tail = raw[1]
            if lead not in params_by_lead:
                params_by_lead[lead] = []
            params_by_lead[lead].append(tail)

        data_packet = Packet()
        for lead, tails in params_by_lead.items():
            data_packet.append(BlaubergProtocol.LEAD_INDICATOR)
            data_packet.append(Section(lead))
            for tail in tails:
                param = (
                    Section(byte_size=2)
                    .set_bytes(Section(lead).to_bytes() + Section(tail).to_bytes())
                    .value
                )
                val = parameters[param]
                if val is not None:
                    data_packet.append(BlaubergProtocol.DYNAMIC_VAL)
                    value_sec = Section(val)
                    data_packet.append(Section(value_sec.byte_size))
                    data_packet.append(Section(tail))
                    data_packet.append(value_sec)
                else:
                    data_packet.append(Section(tail))
        return data_packet

    def read_params(self, parameters: list[int]) -> dict[int, int | None]:
        params = {}
        for param in parameters:
            params[param] = None
        data_response = self._communicate_block(
            self.FUNC.R, self._construct_command_block(params)
        )
        return self._decode_data(data_response.to_bytes())

    def read_param(self, param: int) -> int:
        return self.read_params([param]).get(param) or 0

    def write_params(self, parameters: Mapping[int, int]) -> dict[int, int | None]:
        data_response = self._communicate_block(
            self.FUNC.RW, self._construct_command_block(parameters)
        )
        return self._decode_data(data_response.to_bytes())

    def write_param(self, param: int, value: int) -> int:
        return self.write_params({param: value}).get(param) or 0

    def device_type(self, type_parameter: int = 0xB9) -> int:
        return self.read_param(type_parameter)
