from __future__ import annotations
from enum import Enum
from .blauberg_device import (
    BlaubergDevice,
    Purpose,
    SinglePointAction,
    ComplexAction,
    Component,
    OptionalAction,
    variable_to_bytes,
)
from collections.abc import Mapping
from ezpacket import Packet, Section

import logging

LOG = logging.getLogger(__name__)

_operation_state_params = [0x03, 0x0F, 0x11, 0x12, 0x13, 0x1D, 0x1E, 0x05]


class OperationState(str, Enum):
    ALL_DAY = "all_day"
    HUMIDITY_TRIGGER = "humidity_trigger"
    TEMP_TRIGGER = "temp_trigger"
    MOTION_TRIGGER = "motion_trigger"
    EXT_SWITCH_TRIGGER = "ext_switch_trigger"
    INTERVAL_VENTILATION = "interval_ventilation"
    SILENT = "silent"
    BOOST = "boost"


def _operation_state_response_parser(response: Mapping[int, int | None]) -> str:
    if response.get(0x03) == 1:
        return OperationState.ALL_DAY.value
    if response.get(0x0F) == 1:
        return OperationState.HUMIDITY_TRIGGER.value
    if response.get(0x11) == 1:
        return OperationState.TEMP_TRIGGER.value
    if response.get(0x12) == 1:
        return OperationState.MOTION_TRIGGER.value
    if response.get(0x13) == 1:
        return OperationState.EXT_SWITCH_TRIGGER.value
    if response.get(0x1D) == 1:
        return OperationState.INTERVAL_VENTILATION.value
    if response.get(0x1E) == 1:
        return OperationState.SILENT.value
    if response.get(0x05) == 1:
        return OperationState.BOOST.value
    return "unknown"


def _operation_state_request_parser(
    preset: float | str | int | bool | None,
) -> Mapping[int, int]:
    if not isinstance(preset, str):
        LOG.error("preset is not a string")
        return {}
    reset = {x: 0 for x in _operation_state_params}
    if preset == OperationState.ALL_DAY.value:
        reset.update({0x03: 1})
        return reset
    if preset == OperationState.HUMIDITY_TRIGGER.value:
        reset.update({0x0F: 1})
        return reset
    if preset == OperationState.TEMP_TRIGGER.value:
        reset.update({0x11: 1})
        return reset
    if preset == OperationState.MOTION_TRIGGER.value:
        reset.update({0x12: 1})
        return reset
    if preset == OperationState.EXT_SWITCH_TRIGGER.value:
        reset.update({0x13: 1})
        return reset
    if preset == OperationState.INTERVAL_VENTILATION.value:
        reset.update({0x1D: 1})
        return reset
    if preset == OperationState.SILENT.value:
        reset.update({0x1E: 1})
        return reset
    if preset == OperationState.BOOST.value:
        reset.update({0x05: 1})
        return reset
    return {}


preset_action = ComplexAction(
    parameters=_operation_state_params,
    response_parser=_operation_state_response_parser,
    request_parser=_operation_state_request_parser,
)

version_packet = Packet(
    [
        Section.Template(1),  # major
        Section.Template(1),  # minor
        Section.Template(1),  # day
        Section.Template(1),  # month
        Section.Template(2),  # year
    ]
)

smart_wifi = BlaubergDevice(
    name="Blauberg Smart-WIFI",
    parameter_map={
        Purpose.POWER: SinglePointAction(0x01),
        Purpose.FAN_SPEED: ComplexAction(
            parameters=[0x18],
            response_parser=lambda response: response[0x18],
            # Since this fan model doesn't have support for direct fan control
            # we can set the maximum fan speeds instead
            request_parser=lambda input: {
                0x18: variable_to_bytes(input),
                0x1B: variable_to_bytes(input),
                0x03: 0x01,
                0x1E: 0x00,
                0x04: variable_to_bytes(input),
            },
        ),
        Purpose.MOISTURE_SENSOR: SinglePointAction(0x2E),
        Purpose.TEMPERATURE_SENSOR: SinglePointAction(0x31),
        Purpose.PRESET: preset_action,
        Purpose.VERSION: ComplexAction(
            parameters=[0x86],
            response_parser=lambda response: response[0x86]
            and "%d.%d"
            % (
                Section(response[0x86]).to_bytes()[0],
                Section(response[0x86]).to_bytes()[1],
            ),
            request_parser=lambda _: {},
        ),
    },
    presets=[operation_state.value for operation_state in OperationState],
    extra_parameters=[
        OptionalAction(
            name="Humidity Sensor Trigger Point",
            identifier="humidity_set",
            component=Component.SLIDER,
            action=SinglePointAction(0x14),
            minimum=40,
            maximum=80,
        ),
        OptionalAction(
            name="Temperature Sensor Trigger Point",
            identifier="temp_set",
            component=Component.SLIDER,
            action=SinglePointAction(0x16),
            minimum=18,
            maximum=36,
        ),
        OptionalAction(
            name="Silent Speed Point",
            identifier="silent_set",
            component=Component.SLIDER,
            action=SinglePointAction(0x1A),
            minimum=30,
            maximum=100,
        ),
    ],
    attribute_map={
        "rpm": ComplexAction(
            parameters=[0x04],
            # bytes are swapped for this value
            response_parser=lambda response: response[0x04]
            and response[0x04] << 8 & 0xFF00 | response[0x04] >> 8 & 0x00FF,
            request_parser=lambda _: {},
        )
    },
)
